"""Offline English -> Czech translation with resumable cache and protected markup."""
import argparse, collections, json, os, re, time
from pathlib import Path
import ctranslate2
from transformers import MarianTokenizer
BASE=Path(__file__).resolve().parent
MOD=BASE.parent
NUMBER=r'(?<!\w)[+-]?\d+(?:[.,]\d+)?'
TOKEN=re.compile(r'\{[^{}]+\}|</?[A-Za-z][^>]*>|\b(?:BigChange|SmallChange)\b|(?:https?://|www\.)[^\s<>]+|![a-z]+(?:\s+[A-Z])?|'+NUMBER)
NUMBERS=['ZERO','ONE','TWO','THREE','FOUR','FIVE','SIX','SEVEN','EIGHT','NINE','TEN','ELEVEN','TWELVE','THIRTEEN','FOURTEEN','FIFTEEN','SIXTEEN','SEVENTEEN','EIGHTEEN','NINETEEN','TWENTY','TWENTYONE','TWENTYTWO','TWENTYTHREE','TWENTYFOUR','TWENTYFIVE','TWENTYSIX','TWENTYSEVEN','TWENTYEIGHT','TWENTYNINE']
SENTENCE=re.compile(r'(?<=[.!?])\s+(?=[A-Z0-9"“‘\{<])|\n+')

def token_counts(s):
    # A spelled-out number may legitimately become a digit during translation.
    # Existing digits are still masked and restored exactly like variables.
    return collections.Counter(t for t in TOKEN.findall(s) if not re.fullmatch(r'[+-]?\d+(?:[.,]\d+)?',t))
def simplify(s):
    for a,b in [('making a killing','earning a fortune'),('make a killing','earn a fortune'),('selling like sliced bread','selling extremely well'),('Your Esteemed Highness','Your Majesty'),('Your Greatness','Your Majesty'),('the March','the borderlands'),('The March','The Borderlands'),('Marcher','borderland'),('Grandees','Magnates'),('Grandee','Magnate')]:s=s.replace(a,b)
    return s
def polish(s):
    for a,b in [('Defiance','vzdor'),('defiance','vzdor'),('Monarch','Panovník'),('monarch','panovník'),('magnáti','velmoži'),('Magnáti','Velmoži'),('magnátů','velmožů'),('magnátům','velmožům'),('magnáty','velmože'),('magnátech','velmožích'),('magnát','velmož'),('Magnát','Velmož')]:s=s.replace(a,b)
    return s
def faction_terms(source,target):
    if 'Chiefs' in source:
        terms={'šéfové':'náčelníci','šéfů':'náčelníků','šéfům':'náčelníkům','šéfy':'náčelníky','šéfech':'náčelnících'}
        def replace(m):
            word=m[0];value=terms[word.lower()]
            return value[0].upper()+value[1:] if word[0].isupper() else value
        target=re.sub(r'\b(?:šéfové|šéfů|šéfům|šéfy|šéfech)\b',replace,target,flags=re.I)
    return target
def protect(s):
    masks=[];tags=[];pieces=[];end=0;length=0
    s=simplify(s)
    for m in TOKEN.finditer(s):
        before=s[end:m.start()];pieces.append(before);length+=len(before)
        if m[0].startswith('<'):tags.append((length,m[0]))
        else:
            idx=len(masks);assert idx<len(NUMBERS)
            masks.append(m[0]);marker=' ZXQ'+NUMBERS[idx]+'XZ '
            pieces.append(marker);length+=len(marker)
        end=m.end()
    pieces.append(s[end:])
    return ''.join(pieces),masks,tags
def restore(s,masks):
    for i,value in enumerate(masks):
        code='ZXQ'+NUMBERS[i]+'XZ'
        p=re.compile(r'[\s.,]*'.join(code),re.I)
        matches=list(p.finditer(s))
        if len(matches)!=1:return None
        s=p.sub(lambda _:value,s)
    s=re.sub(r'\s+(</[^>]+>)',r'\1',s)
    s=re.sub(r'(<[^/>]+>)\s+',r'\1',s)
    return s.strip()

def aligned_markup(result,source_offsets,tags):
    tokens=result.hypotheses[0]
    surfaces=[p.replace('▁',' ') if p not in ('<unk>','<pad>','</s>','<s>') else '' for p in tokens]
    boundaries=[0]
    for p in surfaces:boundaries.append(boundaries[-1]+len(p))
    text=''.join(surfaces)
    aligned=[max(range(1,len(a)-1),key=a.__getitem__) for a in result.attention[0]]
    stack=[];events=[]
    def boundary(pos):
        if pos<=0:return 0
        candidates=[i for i,a in enumerate(aligned) if a<len(source_offsets) and source_offsets[a][1]<=pos and source_offsets[a][1]>=0]
        return boundaries[max(candidates)+1] if candidates else 0
    for pos,tag in tags:
        name=re.match(r'</?([\w]+)',tag)[1]
        if tag.startswith('</'):
            match=next((j for j in range(len(stack)-1,-1,-1) if stack[j][2]==name),None)
            if match is None:events.append((boundary(pos),tag));continue
            start,opening,_=stack.pop(match)
            indices=[i for i,a in enumerate(aligned) if a<len(source_offsets) and source_offsets[a][1]>start and source_offsets[a][0]<pos]
            if indices:
                left=min(indices);right=max(indices)+1
                begin=boundaries[left]+(1 if surfaces[left].startswith(' ') else 0)
                events.extend([(begin,opening),(boundaries[right],tag)])
            else:events.extend([(boundary(start),opening),(boundary(pos),tag)])
        elif name in ('br','sprite','space','page'):events.append((boundary(pos),tag))
        else:stack.append((pos,tag,name))
    events.extend((boundary(pos),tag) for pos,tag,name in stack)
    for pos,tag in sorted(events,key=lambda x:x[0],reverse=True):text=text[:pos]+tag+text[pos:]
    return text

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--limit',type=int,default=0);ap.add_argument('--sample',action='store_true');args=ap.parse_args()
    tok=MarianTokenizer.from_pretrained(str(BASE/'model_source'))
    tr=ctranslate2.Translator(str(BASE/'model_ct2'),device='cpu',compute_type='int8',intra_threads=8,inter_threads=1)
    catalog=json.loads((MOD/'catalog.json').read_text(encoding='utf-8'))
    overrides=json.loads((MOD/'manual.json').read_text(encoding='utf-8')) if (MOD/'manual.json').exists() else {}
    rows=[s for s in catalog if s not in overrides]
    if args.sample:rows=[
      'Your Esteemed Highness, I recently arranged for the petrified bones of a long-dead giant to be imported to the Coast from the North. I\'m seeking your blessing to hold a spice festival in its ribcage.',
      'Because last summer {K0} held {K1} festival in an ancient waterfall grove, and I simply must outdo {K2}.',
      'Order {K0} {K1} to return the dead giant to its homeland.',
      'Acquire an <b>Heir</b> then complete your <b>Ambition</b> to win.',
      'The Barons sell a weapon cache to the Tatterlands, making a killing - BigChange wealth!',
      'Your Nobles may now join the game at <b>www.kotc.app</b> using the room code above.'
    ]
    elif args.limit:rows=rows[:args.limit]
    recipes={s:[p for p in SENTENCE.split(s) if p] for s in rows}
    units=list(dict.fromkeys(p for ps in recipes.values() for p in ps))
    cache_path=BASE/'translation-cache-v3.jsonl'
    cache={}
    if cache_path.exists():
        for line in cache_path.read_text(encoding='utf-8').splitlines():
            try:r=json.loads(line);cache[r['en']]=r['cs']
            except ValueError:pass
    for s in units:
        if s in overrides:cache[s]=overrides[s]
    for s in units:
        if not re.search('[A-Za-z]',TOKEN.sub('',s)):cache[s]=s
    pending=sorted((s for s in units if s not in cache),key=len)
    start=time.time();issues=[];done=0
    def translate_batch(samples,markups=None):
        src=[tok.convert_ids_to_tokens(tok.encode('>>ces<< '+s)) for s in samples]
        assert max(map(len,src),default=0)<1024
        results=tr.translate_batch(src,beam_size=3,max_decoding_length=min(768,max(64,max(map(len,src))*3+24)),max_batch_size=2048,batch_type='tokens',repetition_penalty=1.05,return_attention=bool(markups))
        decoded=[]
        for i,r in enumerate(results):
            if markups and markups[i]:
                proto=tok.spm_source.encode(samples[i],return_type='proto')
                offsets=[(-1,-1)]+[(p.begin,p.end) for p in proto.pieces]+[(999999,999999)]
                assert len(offsets)==len(src[i]),(len(offsets),len(src[i]),samples[i])
                decoded.append(aligned_markup(r,offsets,markups[i]))
            else:decoded.append(tok.decode(tok.convert_tokens_to_ids(r.hypotheses[0]),skip_special_tokens=True))
        return decoded
    with cache_path.open('a',encoding='utf-8') as f:
        for begin in range(0,len(pending),96):
            batch=pending[begin:begin+96]
            prepared=[protect(s) for s in batch]
            outputs=translate_batch([x[0] for x in prepared],[x[2] for x in prepared])
            for s,(masked,masks,tags),output in zip(batch,prepared,outputs):
                output=output.replace('<unk>','')
                cs=restore(output,masks)
                ink_marks=re.findall(r'\{K\d+\}',s)
                if cs is not None and ink_marks and (re.findall(r'\{K\d+\}',cs)!=ink_marks or (re.search(r'\{K\d+\}$',s) and not re.search(r'\{K\d+\}\s*$',cs))):cs=None
                if cs is not None and token_counts(s)!=token_counts(cs):cs=None
                if cs is not None and re.findall(r'</?[A-Za-z][^>]*>',s)!=re.findall(r'</?[A-Za-z][^>]*>',cs):cs=None
                if cs is None:
                    # Translate text spans individually if the model changes a marker.
                    parts=TOKEN.split(s);hits=TOKEN.findall(s)
                    nonempty=[p for p in parts if re.search('[A-Za-z]',p)]
                    translated=iter(translate_batch(nonempty));rebuilt=[]
                    for i,p in enumerate(parts):
                        if re.search('[A-Za-z]',p):
                            p=p[:len(p)-len(p.lstrip())]+next(translated).strip()+p[len(p.rstrip()):]
                        rebuilt.append(p)
                        if i<len(hits):rebuilt.append(hits[i])
                    cs=''.join(rebuilt).strip();issues.append({'en':s,'reason':'protected marker required segmented translation'})
                if not cs:raise RuntimeError('Empty translation: '+s)
                cs=polish(cs)
                if token_counts(s)!=token_counts(cs):
                    raise RuntimeError('Markup mismatch: '+s+' => '+cs)
                if re.findall(r'</?[A-Za-z][^>]*>',s)!=re.findall(r'</?[A-Za-z][^>]*>',cs):
                    raise RuntimeError('Markup order mismatch: '+s+' => '+cs)
                cache[s]=cs
                f.write(json.dumps({'en':s,'cs':cs},ensure_ascii=False)+'\n')
            f.flush();done+=len(batch)
            elapsed=time.time()-start
            print(json.dumps({'units_done':done,'units_total':len(pending),'elapsed_s':round(elapsed),'remaining_s':round(elapsed*(len(pending)-done)/max(done,1)),'marker_fallbacks':len(issues)},ensure_ascii=False),flush=True)
    translations={}
    for s in rows:
        ps=SENTENCE.split(s);seps=SENTENCE.findall(s)
        translations[s]=faction_terms(s,''.join((cache[p] if p else '')+seps[i] if i<len(seps) else (cache[p] if p else '') for i,p in enumerate(ps)))
    translations.update(overrides)
    if args.sample:
        for s in rows:print(json.dumps({'en':s,'cs':translations[s]},ensure_ascii=False),flush=True)
    else:
        destination=MOD/'translations.json'
        previous=json.loads(destination.read_text(encoding='utf-8')) if destination.exists() else {}
        previous.update(translations)
        destination.write_text(json.dumps(previous,ensure_ascii=False,indent=2),encoding='utf-8')
    (BASE/'translation-issues.json').write_text(json.dumps(issues,ensure_ascii=False,indent=2),encoding='utf-8')
    print('DONE',len(translations),time.time()-start,flush=True)

if __name__=='__main__':main()
