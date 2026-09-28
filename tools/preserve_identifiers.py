import json,re
from pathlib import Path
mod=Path(__file__).resolve().parents[1]
catalog=json.loads((mod/'catalog.json').read_text(encoding='utf-8'))
manual=json.loads((mod/'manual.json').read_text(encoding='utf-8'))
count=0
for source,context in catalog.items():
    identifier=(' ' not in source and (re.search(r'[A-Za-z]\d|\d[A-Za-z]|[a-z][A-Z]',source) or source.startswith(('^(','[','.*','<mspace=')))) or (context.startswith('code:') and source.startswith(('^(','^[')))
    if identifier and source not in manual:
        manual[source]=source;count+=1
(mod/'manual.json').write_text(json.dumps(manual,ensure_ascii=False,indent=2),encoding='utf-8')
print('Preserved identifier-like strings',count)
