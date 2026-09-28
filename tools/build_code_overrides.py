import json
from pathlib import Path
from translation_text import SENTENCE,assemble,review_display_terms
base=Path(__file__).resolve().parent
manual=json.loads((base.parent/'manual.json').read_text(encoding='utf-8'))
extra=base/'additional-display.json'
if extra.exists():
    extra=json.loads(extra.read_text(encoding='utf-8'))
    manual.update({s:v['translation'] for s,v in extra.items()})
    catalog_path=base.parent/'catalog.json'
    catalog=json.loads(catalog_path.read_text(encoding='utf-8'))
    catalog.update({s:v['context'] for s,v in extra.items()})
    catalog_path.write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
# Keep the rendering dictionary consistent with the reviewed literals used in
# the assembly patch, including corrections made during a long model run.
dictionary=base.parent/'translations.json'
if dictionary.exists():
    values=json.loads(dictionary.read_text(encoding='utf-8'))
    # A reviewed sentence can occur inside many longer catalog paragraphs.
    # Reassemble those paragraphs too, preserving their original separators.
    cache={}
    for line in (base/'translation-cache-v3.jsonl').read_text(encoding='utf-8').splitlines():
        try:row=json.loads(line);cache[row['en']]=row['cs']
        except ValueError:pass
    cache.update(manual)
    for source in json.loads((base.parent/'catalog.json').read_text(encoding='utf-8')):
        parts=SENTENCE.split(source)
        if source not in manual and any(p in manual for p in parts) and all(not p or p in cache for p in parts):
            values[source]=assemble(source,cache)
    values.update(manual)
    values={s:(t if s in manual else review_display_terms(s,t)) for s,t in values.items()}
    dictionary.write_text(json.dumps(values,ensure_ascii=False,indent=2),encoding='utf-8')
rows=json.loads((base/'code_strings.json').read_text(encoding='utf-8'))
overrides=[]
for row in rows:
    name,method,source=row['type'],row['method'],row['text']
    eligible=(name.startswith(('KotC.Scenes.','KotC.UI.','Scenes.Vote.'))
              or name in ('Region','SchemeSteps/SchemeStep','TaxationConfirmationActor','BetweenTurnsScreen','BetweenScreenController','TurnComponent')
              or name=='KotC.Characters.SuccessorGenerator'
              or (name=='KotC.Utils.StringUtilities' and method in ('XOfY','XTooY'))
              or name.startswith(('TwitchConnector/','WebsocketChatConnector/','KotC.Backend.TributaryUserAccount/','KotC.Backend.Clients.Websocket.KingOfTheCastleWebsocketClient/')))
    if name=='Region':eligible=method=='get_SchemeGoalText'
    if name=='SchemeSteps/SchemeStep':eligible=method in ('BoundaryString','TurnRequirementString','GroupingDescription')
    if method=='PluralizeStatName':eligible=False
    if eligible and source in manual and source!=manual[source]:
        overrides.append(dict(row,translation=manual[source]))
(base/'code-overrides.json').write_text(json.dumps(overrides,ensure_ascii=False,indent=2),encoding='utf-8')
print('Reviewed code string occurrences',len(overrides))
