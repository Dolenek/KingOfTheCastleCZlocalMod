"""Reviewed Czech wording for recurring scheme objectives, with original tags."""
import json,re
from pathlib import Path
mod=Path(__file__).resolve().parents[1]
catalog=json.loads((mod/'catalog.json').read_text(encoding='utf-8'))
manual=json.loads((mod/'manual.json').read_text(encoding='utf-8'))
actors={'Chiefs':'náčelníci','Counts':'hrabata','Grandees':'velmoži','Patricians':'patricijové','Barons':'baroni'}
genitives={'Chiefs':'náčelníků','Counts':'hrabat','Grandees':'velmožů','Patricians':'patricijů','Barons':'baronů'}
phrases={
 "lower the combined total of":"snížit celkový součet",
 "lower the other regions'":"snížit v ostatních regionech",
 "lower the Kingdom's":"snížit královskou",
 "the other regions' Farming":"zemědělství ostatních regionů",
 "all regions' combined Farming":"celkové zemědělství všech regionů",
 "all regions' combined Trade":"celkový obchod všech regionů",
 "all regions' Faith":"víry všech regionů",
 "raise all regions' Faith":"zvýšit víru všech regionů",
 "other regions' Defiance":"vzdor ostatních regionů",
 "other regions' Trade":"obchod ostatních regionů",
 "their Military":"své vojsko","their Farming":"své zemědělství",
 "their <b>Faith":"svou <b>víru",
 "their Trade":"svůj obchod","their Defiance":"svůj vzdor","their Faith":"svou víru",
 "the Treasury":"pokladnu","highest Military":"nejvyšší vojsko",
 "highest Trade":"nejvyšší obchod","highest Faith":"nejvyšší víru","highest Farming":"nejvyšší zemědělství",
 "be the region with the":"ve svém regionu dosáhnout",
 "their stat goal is to have the":"mít","have the":"mít",
 "or ensure the current":"nebo zajistit, aby stávající",
 "or ensure another region begins a":"nebo zajistit, aby v jiném regionu vypukla",
 "is still ongoing":"pokračovala","continues":"pokračovala",
 "without starting a rebellion":"bez vyvolání vzpoury",
 "to a combined total of":"na celkový součet","at a combined total of":"na celkovém součtu",
 "for a full season":"po celé jedno roční období","one full season":"celé jedno roční období",
 "of all regions":"ze všech regionů","or less":"nebo méně","or more":"nebo více",
 "at least":"alespoň","seasons":"ročních období",
 "raise":"zvýšit","lower":"snížit","keep":"udržet",
 "Authority":"autoritu","Stability":"stabilitu","Defiance":"vzdor",
 "Trade":"obchod","Faith":"víru","Farming":"zemědělství","Military":"vojsko","Treasury":"pokladnu",
 "Rebellion":"vzpoura","to":"na","at":"na hodnotě","in":"do","for":"po","but":"ale",
}

def objective(source):
 pattern=r"^(?:For the (next|final) stage of their [Ss]cheme, the (Chiefs|Counts|Grandees|Patricians|Barons|\{K\d+\}) must|For the (next|final) stage of the (Chiefs|Counts|Grandees|Patricians|Barons)' Scheme, (?:they must|their stat goal is to)|To advance their Scheme, the (Chiefs|Counts|Grandees|Patricians|Barons) must|For the final stage of our Scheme, we must)\s+"
 m=re.match(pattern,source)
 if not m:return None
 stage=m[1] or m[3] or ('next' if m[5] else 'final')
 actor=m[2] or m[4] or m[5]
 prefix=('V další fázi intriky musejí ' if stage=='next' else 'V závěrečné fázi intriky musejí ')
 prefix=prefix+actors.get(actor,actor)+' ' if actor else 'V závěrečné fázi naší intriky musíme '
 body=source[m.end():]
 if 'be the region with the' in body:
  body=body.replace('highest Faith','nejvyšší víry').replace('highest Farming','nejvyššího zemědělství')
 for en,cs in sorted(phrases.items(),key=lambda x:len(x[0]),reverse=True):
  body=re.sub(r'(?<!\w)'+re.escape(en)+r'(?!\w)',lambda _:cs,body)
 return prefix+body

count=0
for source in catalog:
 target=objective(source)
 if target is not None:
  assert re.findall(r'</?[A-Za-z][^>]*>',source)==re.findall(r'</?[A-Za-z][^>]*>',target)
  assert re.findall(r'\{K\d+\}',source)==re.findall(r'\{K\d+\}',target)
  manual[source]=target;count+=1
 for faction,genitive in genitives.items():
  expected=f"The {faction}' goal is to ensure the {{K0}} wins the rebellion, produces an <b>Heir</b> and completes {{K1}} <b>Ambition</b>."
  if source==expected:
   manual[source]=f'Cílem {genitive} je zajistit pro {{K0}} vítězství ve vzpouře, získání <b>dědice</b> a splnění {{K1}} <b>cíle vlády</b>.'
  loyalty=f"The {faction}' goal is to aid the {{K0}} by countering the other regions' schemes as much as they can. They will win the game if the {{K1}} produces an <b>Heir</b> and completes {{K2}} <b>Ambition</b>."
  if source==loyalty:
   manual[source]=f'Cílem {genitive} je pomáhat {{K0}} a co nejúčinněji mařit intriky ostatních regionů. Vyhrají, pokud {{K1}} získá <b>dědice</b> a splní {{K2}} <b>cíl vlády</b>.'
manual.update({
 "The Counts' aim is to <b>lower their Defiance</b> to <b>{K0} or less</b>.":'Cílem hrabat je <b>snížit svůj vzdor</b> na <b>{K0} nebo méně</b>.',
 'Squeeze every last drop of gold from the Kingdom. (Goal: Raise Own Military)':'Vymačkat z království poslední zlaťák. (Cíl: posílit vlastní vojsko)',
 'Put all these cannons and muskets to good use. (Goal: Raise Own Military)':'Využít všechna ta děla a muškety. (Cíl: posílit vlastní vojsko)',
 'Start manufacturing muskets and cannons to make our military unbeatable. (Goal: Raise Own Military)':'Zahájit výrobu mušket a děl, aby bylo naše vojsko neporazitelné. (Cíl: posílit vlastní vojsko)',
 'Control the {K0} with the threat of assassination. (Goal: Raise Own Military)':'Ovládat {K0} hrozbou atentátu. (Cíl: posílit vlastní vojsko)',
 'Manufacture a food crisis and kidnap the {K0} during the relief efforts. (Goal: Lower Own Farming)':'Vyvolat nedostatek potravin a během pomoci postiženým unést {K0}. (Cíl: snížit vlastní zemědělství)',
 'Racchamassa, the Mad Tyrant, the Cockroach Queen. (Goal: Raise Authority)':'Racchamassa, šílená tyranka a švábí královna. (Cíl: zvýšit autoritu)',
 'Murmuriach, Duke of Greed, the Face of All Coins. (Goal: Raise Treasury)':'Murmuriach, vévoda chamtivosti a tvář všech mincí. (Cíl: naplnit pokladnu)',
 'March on the Capital with the full strength of the New Model Army. (Goal: Raise Military)':'Vytáhnout na Hlavní město s celou silou Nové vzorové armády. (Cíl: posílit vojsko)',
 'March on the Capital with the full strength of the New Model Army. (Goal: Raise Own Military)':'Vytáhnout na Hlavní město s celou silou Nové vzorové armády. (Cíl: posílit vlastní vojsko)',
 'Bankrupt the Kingdom and buy the throne outright. (Goal: Lower Treasury)':'Přivést království na mizinu a trůn si jednoduše koupit. (Cíl: vyprázdnit pokladnu)',
 'Enact a law to prevent the Patricians from buying public property. (Delay Scheme for one season)':'Přijmout zákon, který zabrání patricijům nakupovat veřejný majetek. (Odloží intriku o jedno roční období)',
 'Prevent the Counts from seeking private audiences with the {K0}. (Delay Scheme for one season)':'Zabránit hrabatům v soukromých audiencích u postavy {K0}. (Odloží intriku o jedno roční období)',
 "The Chiefs' goal is to aid the {K0} by countering the other regions' schemes as much as they can. They will win the game if the {K1} produces an <b>Heir</b> and completes {K2} <b>Ambition</b>.":'Cílem náčelníků je pomáhat {K0} a co nejúčinněji mařit intriky ostatních regionů. Vyhrají, pokud {K1} získá <b>dědice</b> a splní {K2} <b>cíl vlády</b>.',
 'completes {K0} <b>Ambition</b>.':'splní {K0} <b>cíl vlády</b>.',
 'Should Nobles get premium seating at Pyreside Chats?':'Mají šlechtici dostat přednostní místa na Besedách u hranice?',
 'Ambition: Spy Network':'Cíl vlády: Špionážní síť','Ambition: Conquest':'Cíl vlády: Dobývání',
 'How can the Chiefs successfully abduct the {K0}?':'Jak mohou náčelníci úspěšně unést {K0}?',
 'How can the Counts successfully abduct the {K0}?':'Jak mohou hrabata úspěšně unést {K0}?',
 "What should the Counts do when they have replaced the {K0}'s closest advisors?":'Co mají hrabata udělat, když se jim podaří nahradit nejbližší poradce postavy {K0}?',
 "What should the Chiefs do when they have replaced the {K0}'s closest advisors?":'Co mají náčelníci udělat, když se jim podaří nahradit nejbližší poradce postavy {K0}?',
 'How should the Chiefs use their alliance with the ice giants to their advantage?':'Jak mají náčelníci využít spojenectví s ledovými obry ve svůj prospěch?',
 'Should the Chiefs stay loyal to {K0} {K1}, or scheme to place their new Claimant, {K2}, on the throne instead?':'Mají náčelníci zůstat věrní vládě {K0} {K1}, nebo připravit intriku a na trůn dosadit nového uchazeče: {K2}?',
 'What should the Chiefs do now they control the Palace Watch?':'Co mají náčelníci udělat teď, když ovládají palácovou stráž?',
 "The Chiefs' stat goal will not be evaluated <b>until the end of next season</b>.":'Splnění cílové hodnoty náčelníků se vyhodnotí <b>až na konci příštího ročního období</b>.',
})
manual.update({f'Scheme - {faction}':f'Intrika – {genitive}' for faction,genitive in genitives.items()})
assert count==187,(count,'Unexpected scheme objective inventory; review changed game data.')
(mod/'manual.json').write_text(json.dumps(manual,ensure_ascii=False,indent=2),encoding='utf-8')
print('Reviewed scheme objectives',count,'manual entries',len(manual))
