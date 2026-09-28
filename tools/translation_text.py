"""Text assembly shared by the model runner and the final manual merge."""
import re
SENTENCE=re.compile(r'(?<=[.!?])\s+(?=[A-Z0-9"“‘{<])|\n+')

def faction_terms(source,target):
    if 'Chiefs' in source:
        terms={'šéfové':'náčelníci','šéfů':'náčelníků','šéfům':'náčelníkům','šéfy':'náčelníky','šéfech':'náčelnících'}
        def replace(m):
            word=m[0];value=terms[word.lower()]
            return value[0].upper()+value[1:] if word[0].isupper() else value
        target=re.sub(r'\b(?:šéfové|šéfů|šéfům|šéfy|šéfech)\b',replace,target,flags=re.I)
    return target

def assemble(source,cache):
    parts=SENTENCE.split(source);separators=SENTENCE.findall(source)
    return faction_terms(source,''.join((cache[p] if p else '')+separators[i] if i<len(separators) else (cache[p] if p else '') for i,p in enumerate(parts)))

GOALS={
 'Authority':'autorita','Faith':'víra','Farming':'zemědělství','Military':'vojsko','Stability':'stabilita','Trade':'obchod',
 'Highest Faith':'nejvyšší víra','Highest Farming':'nejvyšší zemědělství','Lowest Defiance':'nejnižší vzdor',
 'Lower All Faith':'snížit víru ve všech regionech','Lower All Farming':'snížit zemědělství ve všech regionech',
 'Lower All Trade':'snížit obchod ve všech regionech','Lower Authority':'snížit autoritu',
 "Lower Others' Farming":'snížit zemědělství ostatních regionů',"Lower Others' Military":'oslabit vojsko ostatních regionů',
 'Lower Own Defiance':'snížit vlastní vzdor','Lower Own Faith':'snížit vlastní víru','Lower Own Farming':'snížit vlastní zemědělství',
 'Lower Stability':'snížit stabilitu','Lower Treasury':'vyprázdnit pokladnu',
 'Raise Authority':'zvýšit autoritu','Raise Military':'posílit vojsko',"Raise Others' Defiance":'zvýšit vzdor ostatních regionů',
 'Raise Own Defiance':'zvýšit vlastní vzdor','Raise Own Faith':'zvýšit vlastní víru','Raise Own Farming':'zvýšit vlastní zemědělství',
 'Raise Own Military':'posílit vlastní vojsko','Raise Own Trade':'zvýšit vlastní obchod',
 'Raise Stability':'zvýšit stabilitu','Raise Trade':'zvýšit obchod','Raise Treasury':'naplnit pokladnu',
}
DISPLAY_TERMS={
 'Chiefs':'náčelníci','Counts':'hrabata','Grandees':'velmoži','Patricians':'patricijové','Barons':'baroni','Nobles':'šlechtici',
 'Noble':'šlechtic','Treasury':'pokladna','Authority':'autorita','Stability':'stabilita','Defiance':'vzdor',
 'Trade':'obchod','Farming':'zemědělství','Military':'vojsko','Ambition':'cíl vlády','Wealth':'bohatství','Heir':'dědic','Scheme':'intrika',
}
POSSESSIVE_TERMS={'Chiefs':'náčelníků','Counts':'hrabat','Grandees':'velmožů','Patricians':'patricijů','Barons':'baronů','Nobles':'šlechticů'}
TERM_PATTERN=re.compile(r'\b('+'|'.join(DISPLAY_TERMS)+r")(?!\w)(?:'s|')?")
PROTECTED_PARTS=re.compile(r'(<[^>]+>|\{[^{}]+\}|(?:https?://|www\.)[^\s<>]+|![A-Za-z]+)')

def review_display_terms(source,target):
    goal=re.search(r'\(Goal: ([^()]+)\)$',source)
    if goal:
        key=goal[1]
        translated=GOALS.get(key)
        if key.startswith('Aid the '):translated='pomoci '+key[len('Aid the '):]
        if translated:
            target=re.sub(r'\([^()]*\)[.!]?\s*$',lambda _: '(Cíl: '+translated+')',target)
    def term(m):
        key=m[1]
        return POSSESSIVE_TERMS.get(key,DISPLAY_TERMS[key]) if m[0].endswith("'") or m[0].endswith("'s") else DISPLAY_TERMS[key]
    parts=PROTECTED_PARTS.split(target)
    for i in range(0,len(parts),2):
        parts[i]=TERM_PATTERN.sub(term,parts[i])
        if 'Scheme' in source:
            parts[i]=re.sub(r'\b[Ss]chéma\b','intrika',parts[i])
    return ''.join(parts)
