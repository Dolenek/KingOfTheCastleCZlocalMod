import collections,json,re
from pathlib import Path
mod=Path(__file__).resolve().parents[1]
catalog=json.loads((mod/'catalog.json').read_text(encoding='utf-8'))
translations=json.loads((mod/'translations.json').read_text(encoding='utf-8'))
empty_suffixes={'s','es',"'s"}
tokens=lambda s:collections.Counter(re.findall(r'\{[^{}]+\}|</?[A-Za-z][^>]*>|\b(?:BigChange|SmallChange)\b|(?:https?://|www\.)[^\s<>]+|![a-z]+(?:\s+[A-Z])?',s))
tags=lambda s:re.findall(r'</?[A-Za-z][^>]*>',s)
errors=[]
for source in catalog:
 target=translations.get(source)
 if not isinstance(target,str) or (not target and source not in empty_suffixes):errors.append({'source':source,'reason':'missing or empty'});continue
 if 'ZXQ' in target or '<unk>' in target:errors.append({'source':source,'reason':'model mask or unknown token'})
 if tokens(source)!=tokens(target):errors.append({'source':source,'reason':'protected token mismatch'})
 if tags(source)!=tags(target):errors.append({'source':source,'reason':'markup order changed'})
 if re.findall(r'\{K\d+\}',source)!=re.findall(r'\{K\d+\}',target):errors.append({'source':source,'reason':'Ink variable order changed'})
 if re.search(r'\{K\d+\}$',source) and not re.search(r'\{K\d+\}\s*$',target):errors.append({'source':source,'reason':'Ink end boundary changed'})
(mod/'tools/checks-translation-errors.json').write_text(json.dumps(errors,ensure_ascii=False,indent=2),encoding='utf-8')
assert not errors,errors[:10]
report={'source_strings':len(catalog),'source_words':sum(len(s.split()) for s in catalog),'dictionary_entries':len(translations),'missing':0,'protected_tokens_preserved':True,'markup_order_preserved':True}
(mod/'tools/checks-translations.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('TRANSLATION DATA CHECKS PASSED',report)
