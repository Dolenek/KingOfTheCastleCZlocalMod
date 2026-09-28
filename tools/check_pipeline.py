import copy,json,sys
from pipeline import ink_rewrite,MOD,QUOTED
from validate_assets import ink_compare
def translate(s,context):return 'ČESKY '+s
tests=[
 ['ev','str',"^DYN_SANDWICH_NAME == 'Meat and Two Breads'",'/str',{'x()':'fountain','exArgs':1},'/ev','~ret'],
 ['ev','str','^Meat and Two Breads','/str','/ev','~ret'],
 ['ev','str',"^FLAG_A, FLAG_B, FLAG_C, FLAG_D",'/str',{'x()':'fountain','exArgs':1},'/ev'],
 ['ev','str','^Human choice','/str','/ev',{'*':'target','flg':20}],
 ['ev','str','^vote ','/str','str',"^'What should we do with ",'/str','+','str','^NPC.name','/str',{'x()':'fountain','exArgs':1},'+','str',"^?' TARGET",'/str','+','/ev',{'temp=':'vote_string'},'ev',{'VAR?':'vote_string'},{'x()':'fountain','exArgs':1},'pop','/ev'],
 ['^A sentence with ','ev','str','^NPC.name','/str',{'x()':'fountain','exArgs':1},'out','/ev','^.'],
 ['^END'],
 ['ev','str',"^set name 'The example event'",'/str',{'x()':'fountain','exArgs':1},'/ev']
 ,['ev','str','^success 1','/str','/ev',{'*':'outcome','flg':20}]
 ,['ev','str',"^set FAILURE_REPORTER.name 'Expedition Soldier'",'/str',{'x()':'fountain','exArgs':1},'/ev']
]
for index,source in enumerate(tests):
 result=ink_rewrite(source,translate)
 ink_compare(source,result)
 if index<3 or index==6 or index>=8:assert source==result,(index,result)
 else:assert source!=result,(index,result)
 assert ink_rewrite(source,lambda s,c:s)==source
print('Pipeline checks: control strings, returned data, flags, choices, dynamic questions, placeholders, END and event titles passed.')
conditional=['ev','str','^A casket overflowing with sapphires.','/str','str','^KINGDOM.treasury >= 1000','/str',{'x()':'fountain','exArgs':1},'/ev',{'*':'gift','flg':5}]
result=ink_rewrite(conditional,translate)
assert result[2]=='^ČESKY A casket overflowing with sapphires.'
assert result[5]==conditional[5]
ink_compare(conditional,result)
visited=['ev','str','^A magical fire?','/str',{'CNT?':'previous_choice'},'/ev',{'*':'new_choice','flg':21}]
result=ink_rewrite(visited,translate)
assert result[2]=='^ČESKY A magical fire?'
ink_compare(visited,result)
print('Conditional choices: Fountain conditions and visit counters preserved; display text translated.')
description=['ev','str','^A formidable person.','/str','/ev',{'temp=':'SouthSpousePersonalityDesc','re':True}]
result=ink_rewrite(description,translate)
assert result[2]=='^ČESKY A formidable person.'
ink_compare(description,result)
print('Reviewed description variables translated; variable names and assignments preserved.')
inline=['^ KINGDOM.treasury >= 1000 ~ Spend 1000 gold on tall guards. ']
result=ink_rewrite(inline,translate)
assert result[0].split('~',1)[0]==inline[0].split('~',1)[0]
assert result!=inline
ink_compare(inline,result)
print('Inline choice labels localized; embedded comparison conditions preserved.')
joined=['ev','str',"^vote 'Should Nobles get premium seating?'",'/str','str','^ MONARCH','/str','+','/ev',{'temp=':'vote_string'},'ev',{'VAR?':'vote_string'},{'x()':'fountain','exArgs':1},'pop','/ev']
result=ink_rewrite(joined,translate)
ink_compare(joined,result)
wrong=copy.deepcopy(result);wrong[2]=wrong[2].replace('MONARCH','WRONG_TARGET')
try:ink_compare(joined,wrong)
except AssertionError:pass
else:raise AssertionError('Validator accepted a changed vote target')
print('Concatenated vote arguments checked; changes to vote targets rejected.')
from translation_text import review_display_terms
assert review_display_terms('The Chiefs celebrate.','<sprite name=Chiefs> ChiefsChiefs Chiefs')=='<sprite name=Chiefs> ChiefsChiefs náčelníci'
assert review_display_terms('Drain the Kingdom. (Goal: Lower Treasury)','Vyčerpat království. (Cíl: Dolní Treasury)')=='Vyčerpat království. (Cíl: vyprázdnit pokladnu)'
assert review_display_terms('Chiefs {K0}','www.example.com/Chiefs {K0} Chiefs')=='www.example.com/Chiefs {K0} náčelníci'
print('Reviewed display terms preserve identifiers, markup attributes, URLs and placeholders.')
