import time
import ctranslate2
from transformers import MarianTokenizer
from pathlib import Path
root=Path(__file__).resolve().parent
tok=MarianTokenizer.from_pretrained(str(root/'model_source'))
model=ctranslate2.Translator(str(root/'model_ct2'),device='cpu',compute_type='int8',intra_threads=6)
samples=[
 'Your Esteemed Highness, I recently arranged for the petrified bones of a long-dead giant to be imported to the Coast from the North. I\'m seeking your blessing to hold a spice festival in its ribcage.',
 'Because last summer {K0} held {K1} festival in an ancient waterfall grove, and I simply must outdo {K2}.',
 'Order {K0} {K1} to return the dead giant to its homeland.',
 'The Chiefs are honourable warriors renowned for their pagan religion and prowess in combat.',
 'Acquire an <b>Heir</b> then complete your <b>Ambition</b> to win.',
 'The Barons sell a weapon cache to the Tatterlands, making a killing - BigChange wealth!',
 'The Monarch can mark their preferred voting option. If chosen, they gain +1 Authority.',
 'Nobles must vote for their least favourite option, and the option with the least votes will pass.',
 'Your Nobles may now join the game at <b>www.kotc.app</b> using the room code above.',
 'After a skirmish with ice giants, the Chiefs loot 123456 wealth.',
 'Continue', 'New Dynasty','Trade','Treasury','Defiance','the Unassuming',
]
start=time.time()
source=[tok.convert_ids_to_tokens(tok.encode('>>ces<< '+s)) for s in samples]
result=model.translate_batch(source,beam_size=3,max_decoding_length=256,max_batch_size=32)
for s,r in zip(samples,result):
 print(s,'\n =>',tok.decode(tok.convert_tokens_to_ids(r.hypotheses[0]),skip_special_tokens=True),flush=True)
print('elapsed',time.time()-start,flush=True)
