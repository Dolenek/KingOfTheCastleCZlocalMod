"""Run only when the translator is stopped; queue invalid units for regeneration."""
import collections,json,re
from pathlib import Path
base=Path(__file__).resolve().parent
path=base/'translation-cache-v3.jsonl';rows={};removed=[]
tags=lambda s:re.findall(r'</?[A-Za-z][^>]*>',s)
strip=lambda s:re.sub(r'<[^>]+>|\{[^}]+\}|https?://\S+','',s)
nums=lambda s:collections.Counter(re.findall(r'(?<!\w)[+-]?\d+(?:[.,]\d+)?',strip(s)))
for line in path.open(encoding='utf-8'):
 try:r=json.loads(line)
 except ValueError:continue
 a,b=nums(r['en']),nums(r['cs'])
 if tags(r['en'])!=tags(r['cs']) or 'ZXQ' in r['cs'] or '<unk>' in r['cs'] or a-b:
  removed.append(r);continue
 rows[r['en']]=r
path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows.values()),encoding='utf-8')
(base/'cache-repairs.json').write_text(json.dumps(removed,ensure_ascii=False,indent=2),encoding='utf-8')
print('Retained cache',len(rows),'queued repairs',len(removed))
