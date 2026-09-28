"""Inspect Ink expression strings without changing game data."""
import collections,json,re
from pathlib import Path
base=Path(__file__).resolve().parent
catalog=json.loads((base.parent/'catalog.json').read_text(encoding='utf-8'))
rows=collections.defaultdict(set)
def walk(value,path=()):
    if isinstance(value,dict):
        for k,v in value.items():walk(v,path+(k,))
    elif isinstance(value,list):
        frames=[]
        for i,v in enumerate(value):
            if v=='str':frames.append(i)
            elif v=='/str' and frames:
                start=frames.pop()
                text=''.join(x[1:] for x in value[start+1:i] if isinstance(x,str) and x.startswith('^')).strip()
                if text and re.search('[A-Za-z]',text) and not re.match(r'^(define|set|vote|fetch|exists|npc|challenge|pledge)\b',text):
                    if not re.fullmatch(r'[A-Z0-9_.]+',text):rows[text].add('/'.join(map(str,path)))
            if isinstance(v,(list,dict)):walk(v,path+(i,))
for path in (base/'ink-original').glob('*.json'):walk(json.loads(path.read_text(encoding='utf-8')))
result=[{'text':s,'in_catalog':s in catalog,'contexts':sorted(p)} for s,p in sorted(rows.items())]
(base/'literal-frames.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
missing=[r for r in result if not r['in_catalog']]
print('Expression strings:',len(result),'outside translation catalog:',len(missing))
for r in missing[:130]:print(json.dumps(r,ensure_ascii=False))
