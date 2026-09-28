"""Read translation progress without loading or running the model."""
import json,re
from pathlib import Path
base=Path(__file__).resolve().parent
catalog=json.loads((base.parent/'catalog.json').read_text(encoding='utf-8'))
manual=json.loads((base.parent/'manual.json').read_text(encoding='utf-8'))
split=re.compile(r'(?<=[.!?])\s+(?=[A-Z0-9"“‘{<])|\n+')
units={p for s in catalog if s not in manual for p in split.split(s) if p}
cache={}
for line in (base/'translation-cache-v3.jsonl').read_text(encoding='utf-8').splitlines():
    try:r=json.loads(line);cache[r['en']]=r['cs']
    except ValueError:pass
cache.update(manual)
done=units & cache.keys()
words=lambda ss:sum(len(s.split()) for s in ss)
report={'units':len(units),'translated_units':len(done),'unique_source_words':words(units),'translated_unique_source_words':words(done),'remaining_unique_source_words':words(units-done),'percent_by_words':round(100*words(done)/max(1,words(units)),1),'longest_pending_characters':max(map(len,units-cache.keys()),default=0)}
print(json.dumps(report))
