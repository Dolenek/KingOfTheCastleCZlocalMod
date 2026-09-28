using System.Text.Json;
using Mono.Cecil;
using Mono.Cecil.Cil;

if(args.Length < 3) throw new ArgumentException("dump <assembly> <output.json> | patch-tmp <input.dll> <runtime.dll> <output.dll>");
var resolver = new DefaultAssemblyResolver();
resolver.AddSearchDirectory(Path.GetDirectoryName(Path.GetFullPath(args[1]))!);
using var assembly = AssemblyDefinition.ReadAssembly(args[1],new ReaderParameters{AssemblyResolver=resolver});
IEnumerable<TypeDefinition> Types(IEnumerable<TypeDefinition> ts) => ts.SelectMany(t => new[]{t}.Concat(Types(t.NestedTypes)));
if(args[0]=="ids"){
  var rows=new List<object>();
  HashSet<string> Fields(MethodDefinition method,HashSet<string> visited){
    var result=new HashSet<string>();
    if(!method.HasBody || !visited.Add(method.FullName))return result;
    foreach(var i in method.Body.Instructions){
      if(i.Operand is FieldReference field && (i.OpCode==OpCodes.Ldfld || i.OpCode==OpCodes.Ldsfld))result.Add(field.DeclaringType.FullName+"::"+field.Name);
      if(i.Operand is MethodReference reference && reference.DeclaringType.Scope.Name==assembly.MainModule.Name){
        var target=reference.Resolve();if(target is not null)result.UnionWith(Fields(target,visited));
      }
    }
    return result;
  }
  foreach(var t in Types(assembly.MainModule.Types)) foreach(var m in t.Methods.Where(m=>m.Name=="get_Id" && m.HasBody))
    rows.Add(new{type=t.FullName,fields=Fields(m,new HashSet<string>()).Order().ToArray()});
  File.WriteAllText(args[2],JsonSerializer.Serialize(rows,new JsonSerializerOptions{WriteIndented=true}));
  Console.WriteLine($"Audited {rows.Count} ID getters");
}else if(args[0]=="dump"){
  var rows=new List<object>();
  foreach(var t in Types(assembly.MainModule.Types)) foreach(var m in t.Methods.Where(m=>m.HasBody)) foreach(var i in m.Body.Instructions)
    if(i.OpCode==OpCodes.Ldstr) rows.Add(new{type=t.FullName,method=m.Name,text=(string)i.Operand});
  File.WriteAllText(args[2],JsonSerializer.Serialize(rows,new JsonSerializerOptions{WriteIndented=true}));
  Console.WriteLine($"Exported {rows.Count} string occurrences");
}else if(args[0]=="patch-game"){
  var overrides=JsonSerializer.Deserialize<List<CodeTranslation>>(File.ReadAllText(args[3]))!;
  var applied=0;
  foreach(var t in Types(assembly.MainModule.Types)) foreach(var method in t.Methods.Where(m=>m.HasBody))
    foreach(var i in method.Body.Instructions.Where(i=>i.OpCode==OpCodes.Ldstr)){
      var row=overrides.FirstOrDefault(r=>r.type==t.FullName && r.method==method.Name && r.text==(string)i.Operand);
      if(row is not null){i.Operand=row.translation;applied++;}
    }
  foreach(var t in Types(assembly.MainModule.Types)) foreach(var method in t.Methods.Where(m=>m.HasBody && m.Name=="get_Possessive"))
    foreach(var i in method.Body.Instructions.Where(i=>i.OpCode==OpCodes.Ldstr && ((string)i.Operand=="'s" || (string)i.Operand=="'"))) i.Operand="";
  assembly.Write(args[2]);
  Console.WriteLine($"Patched {applied} reviewed interface strings and possessive suffixes; pronoun identifiers remain original");
}else if(args[0]=="patch-tmp"){
  using var runtime=AssemblyDefinition.ReadAssembly(args[2],new ReaderParameters{AssemblyResolver=resolver});
  var rt=runtime.MainModule.Types.Single(t=>t.FullName=="Kotc.Czech.Runtime");
  var localize=assembly.MainModule.ImportReference(rt.Methods.Single(m=>m.Name=="LocalizeForText"));
  var font=assembly.MainModule.ImportReference(rt.Methods.Single(m=>m.Name=="EnsureFont"));
  var loader=assembly.MainModule.ImportReference(runtime.MainModule.Types.Single(t=>t.FullName=="Kotc.Czech.FontLoader").Methods.Single(m=>m.Name=="LoadFontFace"));
  var faceHooks=0;
  foreach(var method in assembly.MainModule.Types.Single(t=>t.FullName=="TMPro.TMP_FontAsset").Methods.Where(m=>m.HasBody))
    foreach(var instruction in method.Body.Instructions)
      if(instruction.OpCode==OpCodes.Call && instruction.Operand is MethodReference call &&
         call.DeclaringType.FullName=="UnityEngine.TextCore.LowLevel.FontEngine" && call.Name=="LoadFontFace" &&
         call.Parameters.Count==2 && call.Parameters[0].ParameterType.FullName=="UnityEngine.Font" && call.Parameters[1].ParameterType.FullName=="System.Int32"){
        instruction.Operand=loader;faceHooks++;
      }
  if(faceHooks==0)throw new InvalidOperationException("No TMP font-face calls found; incompatible assembly or already patched input.");
  var tmp=assembly.MainModule.Types.Single(t=>t.FullName=="TMPro.TMP_Text");
  foreach(var method in tmp.Methods.Where(m=>m.HasBody && ((m.Name=="set_text") || (m.Name=="SetText" && m.Parameters.Count>0 && m.Parameters[0].ParameterType.FullName=="System.String")))){
    var il=method.Body.GetILProcessor(); var first=method.Body.Instructions[0];
    il.InsertBefore(first,il.Create(OpCodes.Ldarg_0));
    il.InsertBefore(first,il.Create(OpCodes.Ldarg_1));
    il.InsertBefore(first,il.Create(OpCodes.Call,localize));
    il.InsertBefore(first,il.Create(OpCodes.Starg,method.Parameters[0]));
    Console.WriteLine("Patched "+method.FullName);
  }
  var parse=tmp.Methods.Single(m=>m.Name=="ParseInputText" && m.HasBody);
  var p=parse.Body.GetILProcessor();var f=parse.Body.Instructions[0];
  p.InsertBefore(f,p.Create(OpCodes.Ldarg_0));p.InsertBefore(f,p.Create(OpCodes.Call,font));
  assembly.Write(args[3]);
  Console.WriteLine($"Patched {faceHooks} dynamic font-face loads for packaged TTF files");
}

record CodeTranslation(string type,string method,string text,string translation);
