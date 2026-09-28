using System.Text.Json;
using Kotc.Czech;
using Mono.Cecil;
using Mono.Cecil.Cil;

void Require(bool condition,string message){ if(!condition) throw new Exception(message); }
if(args.Length<1)throw new ArgumentException("Checks <mod-directory> [ink-json-directory]");
var mod=Path.GetFullPath(args[0]);
var game=Directory.GetParent(mod)!.FullName;
var values=JsonSerializer.Deserialize<Dictionary<string,string>>(File.ReadAllText(Path.Combine(mod,"translations.json")))!;
var localizer=new TextLocalizer(values);
Require(localizer.Localize(null!)==null,"Null handling");
Require(localizer.Localize("")=="","Empty handling");
foreach(var pair in values)Require(localizer.Localize(pair.Key)==pair.Value,"Exact lookup: "+pair.Key);
Require(localizer.Localize("\n  Treasury \t")=="\n  Pokladna \t","Whitespace preservation");
Require(localizer.Localize("<sprite name=Chiefs> Counts")=="<sprite name=Chiefs> Hrabata","Markup attributes preserved");
Require(localizer.Localize("Oddíl tvoří Disciples of the Tenth.")=="Oddíl tvoří Učedníci Desátého.","Data names localized only in display text");
Require(localizer.Localize("<sprite name=Disciples of the Tenth> Counts")=="<sprite name=Disciples of the Tenth> Hrabata","Data names in markup attributes remain unchanged");
Require(localizer.Localize("Na stole leží Footlongs.")=="Na stole leží Třiceticentimetrové sendviče.","Plural dish name rendered in Czech while data stays English");
Require(localizer.Localize("s")=="" && localizer.Localize("es")=="" && localizer.Localize("'s")=="","English grammar suffixes removed");
Require(localizer.Localize("Unlisted fairly long sentence with no translated terms.")=="Unlisted fairly long sentence with no translated terms.","Generic templates must not match every sentence");
var sample=new TextLocalizer(new Dictionary<string,string>{
 ["End {0}"]="Ukončit: {0}",["Spring"]="Jaro",["{0} {1}"]="{1} {0}",
 ["Player {0}, again {0}"]="Hráč {0}, znovu {0}" });
Require(sample.Localize("End Spring")=="Ukončit: Jaro","Recursive parameter lookup");
Require(sample.Localize("Player Honza, again Honza")=="Hráč Honza, znovu Honza","Repeated parameter");
Require(sample.Localize("Player Honza, again Jana")=="Player Honza, again Jana","Repeated parameter equality");
Require(sample.Localize("Untranslated generic paragraph stays intact.")=="Untranslated generic paragraph stays intact.","Generic placeholder rejection");
Console.WriteLine($"Dictionary: {values.Count} exact translations; {localizer.TemplateCount} specific UI templates. Text checks passed.");

IEnumerable<TypeDefinition> Types(IEnumerable<TypeDefinition> ts)=>ts.SelectMany(t=>new[]{t}.Concat(Types(t.NestedTypes)));
var overrides=JsonSerializer.Deserialize<List<CodeTranslation>>(File.ReadAllText(Path.Combine(mod,"tools/code-overrides.json")))!;
var resolver=new DefaultAssemblyResolver();resolver.AddSearchDirectory(Path.Combine(game,"KingOfTheCastle_Data/Managed"));
foreach(var file in new[]{"KotcAssembly.dll","Unity.TextMeshPro.dll"}){
 using var original=AssemblyDefinition.ReadAssembly(Path.Combine(game,"KingOfTheCastle_Data/Managed",file),new ReaderParameters{AssemblyResolver=resolver});
 using var patched=AssemblyDefinition.ReadAssembly(Path.Combine(mod,"patched/KingOfTheCastle_Data/Managed",file),new ReaderParameters{AssemblyResolver=resolver});
 var oldTypes=Types(original.MainModule.Types).ToArray();var newTypes=Types(patched.MainModule.Types).ToArray();
 Require(oldTypes.Length==newTypes.Length,"Type count changed");
 var methods=0;
 foreach(var (oldType,newType) in oldTypes.Zip(newTypes)){
  Require(oldType.FullName==newType.FullName && oldType.Fields.Count==newType.Fields.Count && oldType.Methods.Count==newType.Methods.Count,"Public structure changed");
  foreach(var (oldMethod,newMethod) in oldType.Methods.Zip(newType.Methods)){
   Require(oldMethod.FullName==newMethod.FullName && oldMethod.HasBody==newMethod.HasBody,"Method changed");
   if(!oldMethod.HasBody)continue;
   var prefix=0;
   if(file=="Unity.TextMeshPro.dll" && oldType.FullName=="TMPro.TMP_Text"){
    if(oldMethod.Name=="set_text" || (oldMethod.Name=="SetText" && oldMethod.Parameters.Count>0 && oldMethod.Parameters[0].ParameterType.FullName=="System.String")){
     prefix=4;Require(newMethod.Body.Instructions[0].OpCode==OpCodes.Ldarg_0 && newMethod.Body.Instructions[1].OpCode==OpCodes.Ldarg_1 && newMethod.Body.Instructions[2].OpCode==OpCodes.Call && ((MethodReference)newMethod.Body.Instructions[2].Operand).FullName.Contains("Kotc.Czech.Runtime::LocalizeForText") && newMethod.Body.Instructions[3].OpCode==OpCodes.Starg,"Invalid text hook");
    }else if(oldMethod.Name=="ParseInputText"){
     prefix=2;Require(newMethod.Body.Instructions[0].OpCode==OpCodes.Ldarg_0 && ((MethodReference)newMethod.Body.Instructions[1].Operand).FullName.Contains("Kotc.Czech.Runtime::EnsureFont"),"Invalid font hook");
    }
   }
   var a=oldMethod.Body.Instructions;var b=newMethod.Body.Instructions;
   Require(b.Count==a.Count+prefix,"Instruction count changed in "+oldMethod.FullName);
   string Operand(object? o,IList<Instruction> ins,int shift)=>o switch {
    null=>"",Instruction i=>"branch:"+(ins.IndexOf(i)-shift),Instruction[] ar=>"switch:"+String.Join(",",ar.Select(i=>ins.IndexOf(i)-shift)),
    MemberReference mr=>mr.FullName,ParameterDefinition p=>"parameter:"+p.Index,VariableDefinition v=>"variable:"+v.Index,_=>o.ToString()!};
   for(int i=0;i<a.Count;i++){
    Require(a[i].OpCode==b[i+prefix].OpCode,"Opcode changed: "+oldMethod.FullName);
    var expected=Operand(a[i].Operand,a,0);
    if(file=="KotcAssembly.dll" && a[i].OpCode==OpCodes.Ldstr){
     var row=overrides.FirstOrDefault(r=>r.type==oldType.FullName && r.method==oldMethod.Name && r.text==expected);
     if(row is not null)expected=row.translation;
     if(oldMethod.Name=="get_Possessive" && (expected=="'s" || expected=="'"))expected="";
    }
    Require(expected==Operand(b[i+prefix].Operand,b,prefix),"Unexpected operand change: "+oldMethod.FullName+" at "+i);
   }
   Require(oldMethod.Body.ExceptionHandlers.Count==newMethod.Body.ExceptionHandlers.Count,"Exception handlers changed");methods++;
  }
 }
 Console.WriteLine($"{file}: {methods} method bodies checked; game instructions and branch targets preserved.");
}
if(args.Length>1){
 int stories=0;
 foreach(var path in Directory.EnumerateFiles(args[1],"*.json",SearchOption.AllDirectories)){
  var story=new Ink.Runtime.Story(File.ReadAllText(path));
  Require(story.mainContentContainer!=null,"Invalid Ink root: "+path);stories++;
 }
 Console.WriteLine($"Ink: {stories} story scripts loaded successfully using the game's Ink library.");
}
Console.WriteLine("CODE CHECKS PASSED. The game was not started.");
record CodeTranslation(string type,string method,string text,string translation);
