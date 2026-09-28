import json,time
from pathlib import Path
import ctranslate2
from transformers import MarianTokenizer
base=Path(__file__).resolve().parent
tok=MarianTokenizer.from_pretrained(str(base/'model_source'))
catalog=json.loads((base.parent/'catalog.json').read_text(encoding='utf-8'))
samples=[s for s in catalog if 90<len(s)<160 and '{' not in s and '<' not in s][:96]
source=[tok.convert_ids_to_tokens(tok.encode('>>ces<< '+s)) for s in samples]
for threads in [4,8]:
 translator=ctranslate2.Translator(str(base/'model_ct2'),device='cpu',compute_type='int8',intra_threads=threads)
 size=2048
 start=time.monotonic()
 results=translator.translate_batch(source,beam_size=3,max_decoding_length=192,max_batch_size=size,batch_type='tokens',repetition_penalty=1.05)
 print(json.dumps({'input_tokens':sum(map(len,source)),'threads':threads,'max_batch_tokens':size,'seconds':round(time.monotonic()-start,2),'output_tokens':sum(len(r.hypotheses[0]) for r in results)}),flush=True)
 del translator
