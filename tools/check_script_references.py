import json,re
from pathlib import Path
base=Path(__file__).resolve().parent
queries=set()
def walk(x):
 if isinstance(x,str):yield x
 elif isinstance(x,dict):
  for value in x.values():yield from walk(value)
 elif isinstance(x,list):
  for value in x:yield from walk(value)
for path in (base/'ink-original').glob('*.json'):
 for s in walk(json.loads(path.read_text(encoding='utf-8'))):
  if s.startswith('^') and re.search(r"(?:==|!=|<=|>=|contains|\.match)\s*'",s):queries.add(s)
(base/'script-string-comparisons.json').write_text(json.dumps(sorted(queries),ensure_ascii=False,indent=2),encoding='utf-8')
display=re.compile(r'\.(?:adjective|demonym|territory|name|title|subject|they|them|their|descriptor)\b',re.I)
relevant=[s for s in sorted(queries) if display.search(s)]
print('Distinct string comparisons',len(queries),'display-field dependencies',len(relevant))
for s in relevant:print(s)
