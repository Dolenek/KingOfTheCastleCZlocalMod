"""Read Unicode cmap tables directly; no font or game engine is started."""
import json,struct
from pathlib import Path
mod=Path(__file__).resolve().parents[1]
required='áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ„“–…'
def coverage(file):
 b=file.read_bytes();u16=lambda p:struct.unpack_from('>H',b,p)[0];u32=lambda p:struct.unpack_from('>I',b,p)[0]
 tables={b[12+i*16:16+i*16].decode('ascii'):(u32(20+i*16),u32(24+i*16)) for i in range(u16(4))}
 cmap=tables['cmap'][0];found=set()
 for i in range(u16(cmap+2)):
  platform,encoding,offset=struct.unpack_from('>HHI',b,cmap+4+i*8)
  if platform not in (0,3):continue
  start=cmap+offset;kind=u16(start)
  if kind==4:
   n=u16(start+6)//2;ends=start+14;begins=ends+2*n+2;deltas=begins+2*n;ranges=deltas+2*n
   for ch in required:
    code=ord(ch)
    for seg in range(n):
     lo,hi=u16(begins+2*seg),u16(ends+2*seg)
     if lo<=code<=hi:
      delta=u16(deltas+2*seg);relative=u16(ranges+2*seg)
      glyph=((code+delta)&65535) if not relative else u16(ranges+2*seg+relative+2*(code-lo))
      if relative and glyph:glyph=(glyph+delta)&65535
      if glyph:found.add(ch)
      break
  elif kind==12:
   groups=[struct.unpack_from('>III',b,start+16+j*12) for j in range(u32(start+12))]
   for ch in required:
    code=ord(ch)
    if any(lo<=code<=hi and first+code-lo for lo,hi,first in groups):found.add(ch)
 return ''.join(ch for ch in required if ch not in found)
report={}
for name in ['georgia.ttf','arial.ttf']:
 path=Path('C:/Windows/Fonts')/name
 report[name]={'path':str(path),'missing':coverage(path) if path.exists() else required}
assert any(not row['missing'] for row in report.values()),report
(mod/'tools/checks-fonts.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
