import collections, json, struct, re
from pathlib import Path
import UnityPy
from UnityPy.helpers import TypeTreeHelper
TypeTreeHelper.read_typetree_boost = False
root=Path(__file__).resolve().parents[2]
counts=collections.Counter()
fields=collections.defaultdict(set)
inks=[]
def strings(x,path=()):
    if isinstance(x,str): yield path,x
    elif isinstance(x,dict):
        for k,v in x.items(): yield from strings(v,path+(k,))
    elif isinstance(x,list):
        for i,v in enumerate(x): yield from strings(v,path+(i,))
for path in (root/'KingOfTheCastle_Data/StreamingAssets/aa/StandaloneWindows64').rglob('*.bundle'):
    env=UnityPy.load(str(path))
    for o in env.objects:
        if o.type.name not in ('TextAsset','MonoBehaviour'):continue
        t=o.parse_as_dict()
        if o.type.name=='TextAsset':
            try: j=json.loads(t['m_Script'].lstrip('\ufeff'))
            except Exception:continue
            values=[v[1:] for p,v in strings(j) if v.startswith('^')]
            inks.extend(values)
            if len(inks)<1500:
                print('INK',t['m_Name'],json.dumps(j,ensure_ascii=False)[:4000])
        else:
            for p,v in strings(t):
                if v and p[-1] not in ('m_Name','SerializedBytes','SerializedBytesString','SerializedNodes'):
                    fields['.'.join(str(k) if not isinstance(k,int) else '[]' for k in p)].add(v)
unique=set(inks)
print('INK counts',len(inks),'unique',len(unique),'words',sum(len(s.split()) for s in unique),'chars',sum(map(len,unique)))
for k,vs in sorted(fields.items()):
    print('FIELD',k,'count',len(vs),'sample',list(sorted(vs))[:12])
Path(__file__).resolve().with_name('ink_samples.json').write_text(json.dumps(list(dict.fromkeys(inks)),ensure_ascii=False,indent=2),encoding='utf-8')
