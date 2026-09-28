import collections,json
import UnityPy
from UnityPy.helpers import TypeTreeHelper
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator
from UnityPy.classes import PPtr
from pipeline import ROOT,MOD,paths
TypeTreeHelper.read_typetree_boost=False
failures=json.loads((MOD/'errors-extract.json').read_text(encoding='utf-8'))
by_file=collections.defaultdict(set)
for row in failures:by_file[row['file']].add(row['object'])
generator=TypeTreeGenerator('2021.3.45f1');generator.load_local_game(str(ROOT))
out=[]
for path in paths():
 if path.name not in by_file:continue
 env=UnityPy.load(str(path));env.typetree_generator=generator
 for obj in env.objects:
  if obj.path_id not in by_file[path.name]:continue
  try:
   head=obj.parse_monobehaviour_head()
   script=head.m_Script.deref_parse_as_dict()
   kind=script['m_Namespace']+'.'+script['m_ClassName']
  except Exception as e:kind='unresolved: '+str(e)
  out.append({'file':path.name,'object':obj.path_id,'class':kind})
(MOD/'tools/unsupported-types.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(collections.Counter(r['class'] for r in out),flush=True)
