import base64, hashlib, json, struct
from pathlib import Path
mod=Path(__file__).resolve().parents[1]
root=mod.parent
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
assets=json.loads((mod/'manifest-assets.json').read_text(encoding='utf-8'))
changed_hashes={Path(r['path']).stem.rsplit('_',1)[-1]:r for r in assets if r['path'].endswith('.bundle')}
catalog_rel=Path('KingOfTheCastle_Data/StreamingAssets/aa/catalog.json')
catalog=json.loads((root/catalog_rel).read_text(encoding='utf-8'))
extra=bytearray(base64.b64decode(catalog['m_ExtraDataString']))
pos=0;patched_options=0
while pos<len(extra):
    assert extra[pos]==7,extra[pos]
    pos+=1
    n=extra[pos];pos+=1+n
    n=extra[pos];pos+=1+n
    size=struct.unpack_from('<i',extra,pos)[0];pos+=4
    data=json.loads(extra[pos:pos+size].decode('utf-16-le'))
    record=changed_hashes.get(data.get('m_Hash'))
    if record:
        data['m_Crc']=0
        data['m_BundleSize']=(mod/'patched'/record['path']).stat().st_size
        encoded=json.dumps(data,separators=(',',':'),ensure_ascii=False).encode('utf-16-le')
        assert len(encoded)<=size
        encoded+=b' \x00'*((size-len(encoded))//2)
        extra[pos:pos+size]=encoded;patched_options+=1
    pos+=size
assert pos==len(extra)
assert patched_options==len(changed_hashes),(patched_options,len(changed_hashes))
catalog['m_ExtraDataString']=base64.b64encode(extra).decode('ascii')
target=mod/'patched'/catalog_rel;target.parent.mkdir(parents=True,exist_ok=True)
target.write_text(json.dumps(catalog,separators=(',',':')),encoding='utf-8')
files=[]
# Package only the current build. Earlier experiments can leave staged files
# which no longer contain any eligible changes and must never be installed.
relative_files={Path(r['path']) for r in assets}
relative_files.update({catalog_rel,Path('KingOfTheCastle_Data/Managed/KotcAssembly.dll'),Path('KingOfTheCastle_Data/Managed/Unity.TextMeshPro.dll'),Path('KingOfTheCastle_Data/Managed/Kotc.Czech.dll')})
for rel in sorted(relative_files):
    path=mod/'patched'/rel;assert path.is_file(),path
    original=root/rel
    files.append({'path':str(rel),'original_sha256':sha(original) if original.exists() else None,'patched_sha256':sha(path)})
manifest={'version':'0.1.0-beta','unity_version':'2021.3.45f1','game':'King of the Castle','locale':'cs-CZ','files':files}
(mod/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('Package files',len(files),'bundle options updated',patched_options)
