"""Independent comparison of structure, identifiers, Odin bytes and story control flow."""
import argparse,base64,collections,json,re,struct,time
from pathlib import Path
import UnityPy
from UnityPy.helpers import TypeTreeHelper
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator
from pipeline import ROOT,MOD,ALLOW,odin_strings,display_field,fixed_generator
TypeTreeHelper.read_typetree_boost=False

def require(value,message):
 if not value:raise AssertionError(message)

DISPLAY_COMMAND=re.compile(r'^\^(?:vote\s|set\s+name\s)')
def command_shape(s):
 # Only the first quoted argument of a vote/title command is display text.
 if re.match(r'^(?:vote\s|set\s+name\s)',s):
  return re.sub(r"'((?:\\.|[^'\\])*)'","'<display-string>'",s,count=1)
 return s

def ink_compare(a,b,path=(),command_checked=False):
 require(type(a) is type(b),'Ink type changed: '+str(path))
 if isinstance(a,dict):
  require(a.keys()==b.keys(),'Ink keys changed: '+str(path))
  for key in a:ink_compare(a[key],b[key],path+(key,))
 elif isinstance(a,list):
  require(len(a)==len(b),'Ink instruction count changed: '+str(path))
  # Translation may move a concatenated command's literals into its first
  # caret slot. Compare the complete expression as well as its unchanged
  # instructions, rather than treating each fragment as a full command.
  checked=set();frames=[]
  for end,value in enumerate(a):
   if value=='ev':frames.append(end)
   elif value=='/ev' and frames:
    begin=frames.pop()
    commands=[i for i in range(begin+1,end) if isinstance(a[i],str) and DISPLAY_COMMAND.match(a[i])]
    if commands:
     literals=lambda xs:''.join(v[1:] for v in xs if isinstance(v,str) and v.startswith('^'))
     old=literals(a[begin+1:end]);new=literals(b[begin+1:end])
     require(command_shape(old)==command_shape(new),'Complete Fountain command changed at '+str(path)+': '+repr(old)+' -> '+repr(new))
     checked.update(commands)
  for i,(left,right) in enumerate(zip(a,b)):ink_compare(left,right,path+(i,),i in checked)
 elif isinstance(a,str) and a.startswith('^'):
  require(b.startswith('^'),'Ink literal opcode changed')
  if a.strip()=='^END':require(a==b,'Ink END marker translated')
  if re.fullmatch(r'\^(?:success \d\d?|failure(?: \d\d?)?)',a.strip()):require(a==b,'Challenge outcome token translated')
  if '~' in a:require(a.split('~',1)[0]==b.split('~',1)[0],'Choice condition changed')
  if re.fullmatch(r'\^[A-Z0-9_]+(?:\.[\w.]+)*',a) or ('~' not in a and re.search(r'==|!=|<=|>=|\|\||&&',a)):
   require(a==b,'Ink identifier or comparison expression changed at '+str(path)+': '+repr(a)+' -> '+repr(b))
  if re.match(r'^\^(?:define|DynastyDefine|fetch|set|exists|Update\w+|Set\w+|Create\w+|unlock|lock|kill|capitalize|vote|challenge|pledge|add|remove|select|Rename\w+|npc|NPC|Resolve\w+|Start\w+|End\w+|Declare\w+)\b',a):
   if not command_checked:
    require(command_shape(a[1:])==command_shape(b[1:]),'Fountain command changed at '+str(path)+': '+repr(a)+' -> '+repr(b))
 else:require(a==b,'Ink control instruction, path or value changed: '+str(path))

def odin_compare(a,b):
 old=list(odin_strings(a));new=list(odin_strings(b));require(len(old)==len(new),'Odin entry count changed')
 old_chunks=[];new_chunks=[];last_old=last_new=0
 for (s1,e1,p1,v1),(s2,e2,p2,v2) in zip(old,new):
  require(p1==p2,'Odin path changed')
  names=[n for n in p1 if n]
  eligible=any(n in ALLOW or n=='interjections' for n in names)
  if 'interjections' in names and p1[-1]!='Item1':eligible=False
  if v1!=v2:
   require(eligible,'Odin identifier changed: '+str(p1))
   old_chunks.extend([a[last_old:s1],b'<localized>']);last_old=e1
   new_chunks.extend([b[last_new:s2],b'<localized>']);last_new=e2
 old_chunks.append(a[last_old:]);new_chunks.append(b[last_new:])
 require(b''.join(old_chunks)==b''.join(new_chunks),'Odin non-text bytes changed')

def tree_compare(a,b,path=()):
 require(type(a) is type(b),'Asset field type changed: '+str(path))
 if isinstance(a,dict):
  require(a.keys()==b.keys(),'Asset field names changed')
  for key in a:
   if key=='SerializedBytes' and a[key]!=b[key]:odin_compare(bytes(a[key]),bytes(b[key]))
   else:tree_compare(a[key],b[key],path+(key,))
 elif isinstance(a,list):
  require(len(a)==len(b),'Asset array length changed: '+str(path))
  for i,(left,right) in enumerate(zip(a,b)):tree_compare(left,right,path+(i,))
 elif a!=b:
  require(isinstance(a,str) and display_field(path),'Non-display asset field changed: '+str(path))

def extra_records(blob):
 pos=0
 while pos<len(blob):
  begin=pos;require(blob[pos]==7,'Catalog record type');pos+=1
  n=blob[pos];pos+=1+n;n=blob[pos];pos+=1+n
  size=struct.unpack_from('<i',blob,pos)[0];pos+=4
  obj=json.loads(blob[pos:pos+size].decode('utf-16-le'));pos+=size
  yield begin,pos,obj
 require(pos==len(blob),'Catalog extra blob size')

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--original-only',action='store_true');args=parser.parse_args()
 generator=fixed_generator()
 output=MOD/'tools'/('ink-original' if args.original_only else 'ink-translated');output.mkdir(exist_ok=True)
 if args.original_only:
  files=[p.relative_to(ROOT) for p in (ROOT/'KingOfTheCastle_Data/StreamingAssets/aa/StandaloneWindows64').glob('storyevents*.bundle')]
 else:files=[Path(r['path']) for r in json.loads((MOD/'manifest-assets.json').read_text(encoding='utf-8'))]
 stats=collections.Counter();start=time.monotonic()
 for file in files:
  original=UnityPy.load(str(ROOT/file));original.typetree_generator=generator
  if args.original_only:new_objects=None
  else:
   patched=UnityPy.load(str(MOD/'patched'/file));patched.typetree_generator=generator
   old_objects={(o.assets_file.name,o.path_id):o for o in original.objects}
   new_objects={(o.assets_file.name,o.path_id):o for o in patched.objects}
   require(old_objects.keys()==new_objects.keys(),'Unity object table changed: '+str(file))
  for obj in original.objects:
   other=new_objects[(obj.assets_file.name,obj.path_id)] if new_objects is not None else obj
   require(obj.type==other.type,'Object class changed')
   same=obj.get_raw_data()==other.get_raw_data()
   if obj.type.name=='TextAsset':
    left=obj.parse_as_dict();right=other.parse_as_dict()
    try:j1=json.loads(left['m_Script'].lstrip('\ufeff'))
    except (ValueError,TypeError):j1={}
    if 'inkVersion' in j1:
     j2=json.loads(right['m_Script'].lstrip('\ufeff'))
     try:ink_compare(j1,j2)
     except AssertionError as e:raise AssertionError(left['m_Name']+': '+str(e)) from e
     require(left['m_Name']==right['m_Name'],'Story identifier changed')
     name=re.sub(r'[^A-Za-z0-9_.-]','_',left['m_Name'])
     (output/(name+'-'+str(obj.path_id)+'.json')).write_text(right['m_Script'].lstrip('\ufeff'),encoding='utf-8')
     stats['stories']+=1
     if file.name.startswith('storyevents'):stats['bundle_stories']+=1
    elif not same:require(False,'Non-Ink text asset changed')
   elif not same:
    require(obj.type.name=='MonoBehaviour','Non-text object changed')
    # The staged directory contains only changed files. Its unchanged script
    # dependencies remain in the game directory; use the original schema for
    # both objects, then compare every pointer and non-display value.
    schema=obj._get_typetree_node()
    tree_compare(obj.parse_as_dict(schema),other.parse_as_dict(schema));stats['changed_behaviours']+=1
   if same:stats['unchanged_objects']+=1
   stats['objects']+=1
  print('validated',file.name,dict(stats),round(time.monotonic()-start),flush=True)
 require(stats['bundle_stories']==1005,'Expected all 1005 bundled stories: '+str(stats))
 require(stats['stories']==(1005 if args.original_only else 1008),'Expected bundled and embedded Ink scripts: '+str(stats))
 if not args.original_only:
  path=Path('KingOfTheCastle_Data/StreamingAssets/aa/catalog.json')
  a=json.loads((ROOT/path).read_text(encoding='utf-8'));b=json.loads((MOD/'patched'/path).read_text(encoding='utf-8'))
  for k in a:
   if k!='m_ExtraDataString':require(a[k]==b[k],'Addressables catalog index changed')
  x=base64.b64decode(a['m_ExtraDataString']);y=base64.b64decode(b['m_ExtraDataString']);require(len(x)==len(y),'Catalog offsets changed')
  changes=0
  for (begin,end,v1),(begin2,end2,v2) in zip(extra_records(x),extra_records(y)):
   require((begin,end)==(begin2,end2),'Catalog record offsets changed')
   if v1!=v2:
    require(v2['m_Crc']==0 and v2['m_BundleSize']>0,'Invalid patched bundle options')
    expected=dict(v1);expected['m_Crc']=0;expected['m_BundleSize']=v2['m_BundleSize']
    require(expected==v2,'Non-bundle option changed');changes+=1
  stats['catalog_modified_bundles']=changes
 (MOD/'tools'/('checks-original.json' if args.original_only else 'checks-assets.json')).write_text(json.dumps(dict(stats),indent=2),encoding='utf-8')
 print('ASSET STRUCTURE CHECKS PASSED',dict(stats),flush=True)
if __name__=='__main__':main()
