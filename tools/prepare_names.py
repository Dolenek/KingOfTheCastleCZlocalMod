import csv,io,json
import UnityPy
from UnityPy.helpers import TypeTreeHelper
from pathlib import Path
TypeTreeHelper.read_typetree_boost=False
mod=Path(__file__).resolve().parent.parent
manual=json.loads((mod/'manual.json').read_text(encoding='utf-8'))
catalog=json.loads((mod/'catalog.json').read_text(encoding='utf-8'))
env=UnityPy.load(str(mod.parent/'KingOfTheCastle_Data/resources.assets'))
credits=next(o.parse_as_dict()['m_Script'] for o in env.objects if o.type.name=='TextAsset' and o.peek_name()=='CreditsData')
for row in csv.reader(io.StringIO(credits)):
    if row and row[0]:catalog.setdefault(row[0],'runtime:credits heading')
    for name in row[1:]:
        if name and len(name)<60 and '\\n' not in name and len(name.split())<7:manual[name]=name
manual.update({'TRIBUTARY GAMES':'TRIBUTARY GAMES','TEAM17':'TEAM17','Team17':'Team17','A':'A','B':'B','C':'C','D':'D','E':'E','AP':'AP','VP':'VB','DEBUG':'DEBUG','LONGNAMETEST1':'LONGNAMETEST1',
 'he':'on','she':'ona','they':'oni','him':'ho','her':'ji','his':'jeho','hers':'její','their':'jejich','theirs':'jejich','himself':'sebe','herself':'sebe','themselves':'sebe',
 'Lord':'Pán','Lady':'Paní','Duke':'Vévoda','Duchess':'Vévodkyně','Sir':'Sir','Dame':'Dáma','Archbishop':'Arcibiskup','Chancellor':'Kancléř','Spymaster':'Mistr špehů','Treasurer':'Pokladník','Marshal':'Maršál'})
(mod/'manual.json').write_text(json.dumps(manual,ensure_ascii=False,indent=2),encoding='utf-8')
(mod/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
print('manual strings',len(manual),'catalog',len(catalog))
