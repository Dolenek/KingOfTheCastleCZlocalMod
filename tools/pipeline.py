"""Extract and patch display text while preserving Unity, Odin, Ink and Fountain structure."""
import argparse, collections, copy, hashlib, json, re, shutil, struct, sys, time
from pathlib import Path
import UnityPy
from UnityPy.helpers import TypeTreeHelper
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator
from UnityPy.helpers.Tpk import get_typetree_node
from UnityPy.helpers.UnityVersion import UnityVersion
from UnityPy.streams import EndianBinaryWriter
TypeTreeHelper.read_typetree_boost = False
MOD=Path(__file__).resolve().parents[1]
ROOT=MOD.parent
DATA=ROOT/'KingOfTheCastle_Data'
ALLOW={'m_text','m_Text','text','title','description','displayName','displayLabel','buildingName','characterName','kingdomName','storyEventName','schemeName','variantName','territoryName','territoryNameUI','demonym','adjective','regionDescription','descriptors','wealthBumpReasons','webModeText','message','tooltip','label','screenDisplayName','instructions','placeholder','challengeDescription','ambitionDescription','subjectPronoun','objectPronoun','possessivePronoun','independentPossessivePronoun','reflexivePronoun'}
ALLOW.discard('subjectPronoun') # HE/SHE/THEY also create named Fountain references.
ALLOW.discard('territoryName') # The same value is exposed to scripted queries.
ALLOW.discard('kingdomName') # KingdomDefinition.Id is the same string.
ALLOW.update({'labelFormat','twitchModeText','generalComment','defaultBlurbText'})
NO_TRANSLATE={'END','end','King of the Castle','Steam','Twitch','Discord','YouTube','Twitter','OK','kotc.app'}
COMMAND=re.compile(r'^(?:define|DynastyDefine|fetch|set|exists|Update\w+|Set\w+|Create\w+|unlock|lock|kill|capitalize|vote|challenge|pledge|add|remove|select|Rename\w+|npc|NPC|Resolve\w+|Start\w+|End\w+|Declare\w+)\b|^[A-Z][A-Z0-9_]*(?:\.[A-Za-z][\w.]*)+(?:\s|$)')
QUOTED=re.compile(r"'((?:\\.|[^'\\])*)'")
# Reviewed Ink variables holding prose, portraits, dialogue or choice labels.
# Entity names, cult names, weapon/item IDs and command construction variables
# remain data literals, because other story branches may compare their values.
DISPLAY_VARIABLES=frozenset('''AccusationString Barons_WhereSpouseIs Brash_Interest_Talk
Charming_Hook_Talk Charming_Interest_Talk CoastFinally CoastGuardsDesc
CoastSpouseInterestDesc CoastSpousePersonalityDesc CoastSpousePlotHookDesc
CostumeReaction Counts_WhereSpouseIs Counts_WhereSpouseIs2 CrowOrigin
EastGuardsDesc EastSpouseInterestDesc EastSpousePersonalityDesc EastSpousePlotHookDesc
EffigyDescription EntertainerAssessment FireHazard FirstDescriptionBit FirstVoteString
GhoulDeath Gladiator1HistoryText Gladiator2HistoryText Grand_WhereSpouseIs
Grand_WhereSpouseIs2 HonourGuardText HubrisReason JointStatement2 MarchFinally
MarchGuardsDesc MarchSpouseInterestDesc MarchSpousePersonalityDesc MarchSpousePlotHookDesc
MirrorDesc NorthGuardsDesc NorthSpouseInterestDesc NorthSpousePersonalityDesc
NorthSpousePlotHookDesc OverwhelmedCoastDesc OverwhelmedEastDesc OverwhelmedMarchDesc
OverwhelmedNorthDesc OverwhelmedSouthDesc PROPH_spouseActivity Pats_WhereSpouseIs
Pats_WhereSpouseIs2 Pomp_Interest_Talk PreambleGuards RegionWatchType
SecondDescriptionBit SecondVoteString SetUpCampLocation Shy_Interest_Talk SoldiersDesc
SouthFinally SouthGuardsDesc SouthSpouseInterestDesc SouthSpousePersonalityDesc
SouthSpousePlotHookDesc SpouseActivity SpouseLocation StatueDesc ThirdVoteString
VisitorTypes WhereSpouseIs WhereSpouseIs2 WireDesc WorkerTypes World_Trophy
additionalPhrase announcer_desc apprenticedesc baron_WhereSpouseIs2 bear_complaint
besmircherRiposte coastVaugarProblem coastVaugarSolution coins conspiracyDesc
deathSentence droppedBy duellistAccusation duellistQuestion duellistResponse
eastVaugarProblem eastVaugarSolution excursion_type execution guarddesc inquisitorScandal
interestTopic interestTopicString introductionFailureString introductionSuccessString
jailbreak_reason lawEnforcement marchVaugarProblem marchVaugarSolution
monarch_schemeloss_str northVaugarProblem northVaugarSolution ominous ravineAction
readingWeather reasonForWar rebel_region_3_str regionalTrophy revenge_desc_1
revenge_desc_2 southVaugarProblem southVaugarSolution spouseActivity
spouseActivity_Heretical spouseCoping spouseCoping2 spouseCoping3 tippedStatue trail
troop_action troop_kill weaponDescriptionString wizardTitle wizard_continue
wizard_desc_1 wizard_desc_2 wizard_experiments wizard_troops wizard_valuables'''.split())

class FixedTypeTreeGenerator(TypeTreeGenerator):
    def get_nodes_up(self,assembly,fullname):
        node=super().get_nodes_up(assembly,fullname)
        # TypeTreeGeneratorAPI omits the enabled-byte alignment and labels some
        # primitive lists with the scalar type. Use Unity's native base header.
        if [c.m_Name for c in node.m_Children[:4]]==['m_GameObject','m_Enabled','m_Script','m_Name']:
            head=get_typetree_node(114,UnityVersion.from_str('2021.3.45f1'))
            node.m_Children=list(head.m_Children)+node.m_Children[4:]
        for child in node.traverse():
            if child.m_Children and child.m_Children[0].m_Type=='Array' and child.m_Type in TypeTreeHelper.FUNCTION_READ_MAP:
                element=child.m_Children[0].m_Children[1]
                if child.m_Type=='string' and element.m_Type=='char':continue
                child.m_Type='vector'
        return node

def fixed_generator():
    generator=FixedTypeTreeGenerator('2021.3.45f1');generator.load_local_game(str(ROOT));return generator

def paths():
    return sorted(list(DATA.glob('*.assets'))+list(DATA.glob('level*'))+list((DATA/'StreamingAssets/aa/StandaloneWindows64').rglob('*.bundle')))

def walk(x,p=()):
    if isinstance(x,str): yield p,x
    elif isinstance(x,dict):
        for k,v in x.items():
            if k not in ('SerializedBytes','SerializedNodes','m_FontData'):
                yield from walk(v,p+(k,))
    elif isinstance(x,list):
        for i,v in enumerate(x): yield from walk(v,p+(i,))

def put(x,p,v):
    for k in p[:-1]: x=x[k]
    x[p[-1]]=v

def human(s):
    s=s.strip()
    if not re.search(r'[A-Za-z]',s) or s in NO_TRANSLATE: return False
    if re.fullmatch(r'[\w]+[._/\\][\w./\\]+',s): return False
    if s.startswith(('http','www.','{','Assets/','Unity','System.')) and not ' ' in s: return False
    return True

def raw_strings(o):
    b=o.get_raw_data();end=len(b)
    for p in range(0,end-8,4):
        n=struct.unpack_from('<i',b,p)[0]
        if not 2<=n<=min(12000,end-p-4):continue
        try:s=b[p+4:p+4+n].decode('utf-8')
        except UnicodeDecodeError:continue
        if '\x00' not in s and all(c.isprintable() or c in '\n\r\t' for c in s) and human(s):yield s

def display_field(p):
    names=[k for k in p if isinstance(k,str)]
    return any(k in ALLOW for k in names) and not any(k in ('m_PersistentCalls','m_Calls','references','SerializedNodes') for k in names)

def odin_strings(b):
    """Walk the actual binary entries, including nodes and length-prefixed strings."""
    p=0;stack=[]
    def string():
        nonlocal p
        start=p;wide=b[p];n=struct.unpack_from('<i',b,p+1)[0];p+=5
        assert wide in (0,1) and 0<=n<2000000
        end=p+n*(2 if wide else 1);assert end<=len(b)
        s=b[p:end].decode('utf-16-le' if wide else 'latin-1');p=end
        return start,end,s
    def type_entry():
        nonlocal p
        tag=b[p];p+=1
        if tag==47:p+=4;string()
        elif tag==48:p+=4
        else:assert tag==46,tag
    named={1,3,9,11,13,15,17,19,21,23,25,27,29,31,33,35,37,39,41,43,45,50}
    sizes={9:4,10:4,11:4,12:4,13:16,14:16,15:1,16:1,17:1,18:1,19:2,20:2,21:2,22:2,23:4,24:4,25:4,26:4,27:8,28:8,29:8,30:8,31:4,32:4,33:8,34:8,35:16,36:16,37:2,38:2,41:16,42:16,43:1,44:1}
    while p<len(b):
        tag=b[p];p+=1;name=string()[2] if tag in named else None
        if tag in (1,2,3,4):
            type_entry()
            if tag in (1,2):p+=4
            stack.append(name)
        elif tag==5:stack.pop()
        elif tag==6:p+=8;stack.append('[]')
        elif tag==7:stack.pop()
        elif tag==8:
            n,size=struct.unpack_from('<ii',b,p);p+=8+n*size
        elif tag in (39,40):
            start,end,s=string();yield start,end,tuple(stack)+(name,),s
        elif tag in sizes:p+=sizes[tag]
        elif tag in (45,46):pass
        elif tag in (50,51):string()
        elif tag==49:assert p==len(b)
        else:raise ValueError(f'Odin entry {tag} at {p-1}')
    assert p==len(b)

def odin_rewrite(b,cb):
    changes=[]
    for start,end,path,s in odin_strings(b):
        names=[x for x in path if x]
        eligible=any(x in ALLOW or x=='interjections' for x in names)
        # Interjection dictionary keys are routing identifiers, tuple Item1 is the text.
        if 'interjections' in names and path[-1]!='Item1':eligible=False
        if eligible and human(s):
            t=cb(s,'odin:'+str(path))
            if t!=s:
                encoded=t.encode('utf-16-le'); changes.append((start,end,b'\x01'+struct.pack('<i',len(encoded)//2)+encoded))
    for start,end,encoded in reversed(changes):b=b[:start]+encoded+b[end:]
    return b

def command_rewrite(s,cb):
    def quote(m):
        text=m[1].replace("\\'","'").replace('\\\\','\\')
        if len(text.split())>=4 or '?' in text or s.lstrip().startswith('set name '):
            t=cb(text,'fountain:quoted display string')
            return "'"+t.replace('\\','\\\\').replace("'","\\'")+"'"
        return m[0]
    return QUOTED.sub(quote,s)

def fountain_rewrite(node,cb):
    """Symbolically follow string concatenation, without evaluating game code.

    Only event titles and vote questions are display arguments. Comparisons,
    flag lists, identifiers and all other Fountain arguments remain literal.
    Each rope item is either an original caret instruction or an opaque value.
    """
    node=list(node);stack=[];variables={};i=0
    def rewrite(rope):
        source='';spans=[[]];markers=[]
        for text,index in rope:
            if index is None:
                marker='{K'+str(len(markers))+'}';source+=marker;markers.append(marker);spans.append([])
            else:source+=text;spans[-1].append(index)
        if not re.match(r"^(?:vote\s|set\s+name\s)",source):return
        def quote(m):
            raw=m[1].replace("\\'","'").replace('\\\\','\\')
            if not human(raw):return m[0]
            translated=cb(raw,'fountain:complete display argument')
            return "'"+translated.replace('\\','\\\\').replace("'","\\'")+"'"
        target=QUOTED.sub(quote,source)
        if source==target:return
        if re.findall(r'\{K\d+\}',target)!=markers:raise ValueError('Changed Fountain placeholder order: '+source)
        parts=re.split(r'\{K\d+\}',target)
        for span,part in zip(spans,parts):
            if not span:
                if part:raise ValueError('Changed Fountain placeholder boundary: '+source)
                continue
            node[span[0]]='^'+part
            for index in span[1:]:node[index]='^'
    while i<len(node):
        value=node[i]
        if value=='str':
            begin=i;depth=1;j=i+1;rope=[]
            while j<len(node) and depth:
                part=node[j]
                if part=='str':depth+=1
                elif part=='/str':depth-=1
                elif depth==1 and isinstance(part,str) and part.startswith('^'):rope.append((part[1:],j))
                elif depth==1 and part=='ev':
                    d=1;k=j+1
                    while k<len(node) and d:
                        if node[k]=='ev':d+=1
                        elif node[k]=='/ev':d-=1
                        k+=1
                    rope.append((None,None));j=k-1
                j+=1
            if depth:stack=[];i+=1;continue
            stack.append(rope);i=j;continue
        if isinstance(value,dict) and 'x()' in value:
            count=value.get('exArgs',1)
            argument=stack.pop() if stack else [(None,None)]
            for _ in range(max(0,count-1)):
                if stack:stack.pop()
            if value['x()']=='fountain' and count==1:rewrite(argument)
            stack.append([(None,None)])
        elif value=='+':
            if len(stack)>=2:
                right=stack.pop();left=stack.pop();stack.append(left+right)
            else:stack=[]
        elif isinstance(value,dict) and ('temp=' in value or 'VAR=' in value):
            variables[value.get('temp=',value.get('VAR='))]=stack.pop() if stack else [(None,None)]
        elif isinstance(value,dict) and 'VAR?' in value:stack.append(variables.get(value['VAR?'],[(None,None)]))
        elif isinstance(value,dict) and 'f()' in value:stack.append([(None,None)])
        elif value=='/ev':pass
        elif value in ('ev','pop','out') or isinstance(value,(list,dict)):stack=[]
        i+=1
    return node

def ink_rewrite(node,cb):
    if isinstance(node,dict):
        return {k:ink_rewrite(v,cb) for k,v in node.items()}
    if not isinstance(node,list):return node
    node=fountain_rewrite(node,cb)
    protected=set();frames=[]
    for i,v in enumerate(node):
        if v=='str':frames.append(i)
        elif v=='/str' and frames:
            start=frames.pop();protected.update(range(start,i+1))
    # Ink puts a conditional value above the choice text on its evaluation
    # stack. A string can therefore be a displayed choice even when another
    # string, a Fountain call or a visit counter follows its closing /str.
    # Follow stack provenance and only release the values actually consumed
    # as choice text or written to the output stream.
    stack=[];i=0;display=set()
    def pop():return stack.pop() if stack else set()
    binary={'+','-','*','/','%','==','!=','>','<','>=','<=','&&','||','?','!?','^','MIN','MAX','POW'}
    unary={'!','_','INT','FLOAT','FLOOR','CEILING'}
    while i<len(node):
        value=node[i]
        if value=='str':
            depth=1;j=i+1;indices=set()
            while j<len(node) and depth:
                part=node[j]
                if part=='str':depth+=1
                elif part=='/str':depth-=1
                elif depth==1 and isinstance(part,str) and part.startswith('^'):indices.add(j)
                j+=1
            stack.append(indices);i=j;continue
        if isinstance(value,dict) and '*' in value:
            flags=value.get('flg',0)
            if flags&1:pop() # condition, never display text
            if flags&4:display.update(pop())
            if flags&2:display.update(pop())
        elif isinstance(value,dict) and 'x()' in value:
            for _ in range(value.get('exArgs',1)):pop()
            stack.append(set())
        elif isinstance(value,dict) and ('VAR?' in value or 'CNT?' in value or 'f()' in value):stack.append(set())
        elif isinstance(value,dict) and ('temp=' in value or 'VAR=' in value):
            spans=pop()
            if value.get('temp=',value.get('VAR=')) in DISPLAY_VARIABLES:display.update(spans)
        elif value=='out':display.update(pop())
        elif value=='du':stack.append(set(stack[-1]) if stack else set())
        elif value=='pop':pop()
        elif isinstance(value,str) and value in binary:
            right=pop();left=pop();stack.append(left|right if value=='+' else set())
        elif isinstance(value,str) and value in unary:pop();stack.append(set())
        elif isinstance(value,(int,float)):stack.append(set())
        i+=1
    protected.difference_update(display)
    def visible(i):
        v=node[i]
        if not isinstance(v,str) or not v.startswith('^') or i in protected:return False
        if re.fullmatch(r'(?:success \d\d?|failure(?: \d\d?)?)',v[1:].strip()):return False
        if '~' in v and human(v.split('~',1)[1]):return True
        return not COMMAND.search(v[1:].strip()) and not re.fullmatch(r'[A-Z0-9_]+(?:\.[\w.]+)*',v[1:].strip())
    def dynamic_end(i):
        if node[i]!='ev':return None
        depth=0
        for j in range(i,len(node)):
            if node[j]=='ev':depth+=1
            elif node[j]=='/ev':
                depth-=1
                if depth==0:return j+1 if j>i and node[j-1]=='out' else None
        return None
    result=[];i=0
    while i<len(node):
        if visible(i):
            start=i;source='';blocks=[];literal_spans=[[]]
            while i<len(node):
                if visible(i):source+=node[i][1:];literal_spans[-1].append(i);i+=1
                elif (end:=dynamic_end(i)) is not None:
                    source+='{K'+str(len(blocks))+'}';blocks.append(node[i:end]);literal_spans.append([]);i=end
                else:break
            prefix=''
            if '~' in source:
                prefix,source=source.split('~',1);prefix+='~'
            if source.strip()=='END':target=source
            elif human(source):target=cb(source,'ink:sentence with dynamic values')
            else:target=source
            target=prefix+target
            if collections.Counter(re.findall(r'\{K\d+\}',target))!=collections.Counter(re.findall(r'\{K\d+\}',prefix+source)):
                raise ValueError('Changed Ink placeholders: '+source)
            if re.findall(r'\{K\d+\}',target)!=re.findall(r'\{K\d+\}',prefix+source):raise ValueError('Changed Ink placeholder order: '+source)
            translated_parts=re.split(r'\{K\d+\}',target)
            replacement=list(node[start:i])
            for span,part in zip(literal_spans,translated_parts):
                if not span:
                    if part.strip():raise ValueError('Changed Ink placeholder boundary: '+source)
                    continue
                replacement[span[0]-start]='^'+part
                for idx in span[1:]:replacement[idx-start]='^'
            result.extend(replacement)
        else:
            v=node[i]
            if not (isinstance(v,str) and v.startswith('^')):v=ink_rewrite(v,cb)
            result.append(v);i+=1
    assert len(result)==len(node),'Ink instruction count changed'
    return result

def transform_object(o,t,cb):
    if o.type.name=='TextAsset':
        text=t['m_Script'];bom='\ufeff' if text.startswith('\ufeff') else ''
        try:j=json.loads(text.lstrip('\ufeff'))
        except (ValueError,TypeError):return t
        if 'inkVersion' in j:
            j=ink_rewrite(j,cb);t['m_Script']=bom+json.dumps(j,ensure_ascii=False,separators=(',',':'))
        return t
    for p,s in list(walk(t)):
        if display_field(p) and human(s):
            translated=cb(s,'asset:'+'.'.join(map(str,p)))
            if p[-1]=='possessivePronoun' and s=='her':translated='její'
            put(t,p,translated)
    od=t.get('serializationData',{})
    if od.get('SerializedBytes'):
        od['SerializedBytes']=list(odin_rewrite(bytes(od['SerializedBytes']),cb))
    return t

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def process(mode):
    catalog={};fields=collections.defaultdict(set);errors=[];stats=collections.Counter()
    if mode=='build':
        translations=json.loads((MOD/'translations.json').read_text(encoding='utf-8'))
        def cb(s,context):
            key=s.strip();v=translations.get(key)
            if v is None:raise KeyError('Missing translation: '+key)
            return s[:len(s)-len(s.lstrip())]+v+s[len(s.rstrip()):]
    else:
        def cb(s,context):
            key=s.strip()
            if key and key not in NO_TRANSLATE:catalog.setdefault(key,context)
            return s
    generator=fixed_generator()
    manifest=[];start=time.time()
    for file in paths():
        env=UnityPy.load(str(file));env.typetree_generator=generator;changed=0
        for o in env.objects:
            if o.type.name not in ('MonoBehaviour','TextAsset'):continue
            try:
                t=o.parse_as_dict()
                if mode=='extract':
                    for p,s in walk(t):
                        if human(s) and p[-1]!='m_Name':fields['.'.join(k if isinstance(k,str) else '[]' for k in p)].add(s)
                before=o.get_raw_data();original=copy.deepcopy(t)
                t=transform_object(o,t,cb)
                if mode=='build' and t!=original:
                    writer=EndianBinaryWriter(endian=o.reader.endian)
                    TypeTreeHelper.write_typetree(original,o._get_typetree_node(),writer,o.assets_file)
                    if writer.bytes!=before:raise ValueError('Non-lossless type tree roundtrip')
                    # ObjectReader.get_raw_data() reads the original stream even
                    # after patch(); save_typetree returns the bytes to be saved.
                    if o.patch(t)!=before:changed+=1
                stats[o.type.name]+=1
                if mode=='build' and o.type.name=='TextAsset' and stats['TextAsset']%200==0:
                    print('story progress',stats['TextAsset'],'/',1011,f'{time.time()-start:.0f}s',flush=True)
            except Exception as e:
                # Unsupported behaviours stay byte-for-byte intact; their display strings
                # are translated by the separate TextMeshPro rendering hook.
                if mode=='extract':
                    for s in raw_strings(o):cb(s,'runtime:unsupported behaviour '+file.name)
                known_parse_failure=any(part in str(e) for part in ('Expected to read','failed to dump nodes raw','Negative length read','unpack requires a buffer','read exceeded'))
                errors.append({'file':file.name,'object':o.path_id,'error':str(e)[:500],'handled_by':'runtime rendering hook' if known_parse_failure else 'fatal'})
        if mode=='build' and changed:
            rel=file.relative_to(ROOT)
            target=MOD/'patched'/rel;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(env.file.save(packer='lz4') if file.suffix=='.bundle' else env.file.save())
            manifest.append({'path':str(rel),'original_sha256':sha(file),'patched_sha256':sha(target),'objects':changed})
        print(mode,file.name,'strings',len(catalog),'changed',changed,'errors',len(errors),f'{time.time()-start:.0f}s',flush=True)
    if mode=='extract':
        code=json.loads((MOD/'tools/code_strings.json').read_text(encoding='utf-8'))
        for row in code:
            if human(row['text']):cb(row['text'],'code:'+row['type']+'.'+row['method'])
        for text in ('END','Chiefs','Counts','Grandees','Patricians','Barons','Spring','Summer','Autumn','Winter','He/Him','She/Her','They/Them','King','Queen','Monarch','Noble','Nobles','Stability','Treasury','Authority','Defiance'):
            catalog.setdefault(text,'runtime:display term')
        (MOD/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
        (MOD/'tools/field_inventory.json').write_text(json.dumps({k:sorted(v) for k,v in fields.items()},ensure_ascii=False,indent=2),encoding='utf-8')
    else:
        if stats['TextAsset']<1005 or not any('storyevents' in r['path'] for r in manifest):
            errors.append({'error':'Expected changed story bundles were not saved','handled_by':'fatal'})
        (MOD/'manifest-assets.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    (MOD/('errors-'+mode+'.json')).write_text(json.dumps(errors,ensure_ascii=False,indent=2),encoding='utf-8')
    print('TOTAL',dict(stats),'unique',len(catalog),'words',sum(len(x.split()) for x in catalog),'errors',len(errors),flush=True)
    if mode=='build' and any(e['handled_by']=='fatal' for e in errors):sys.exit(1)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['extract','build']);args=ap.parse_args();process(args.mode)
