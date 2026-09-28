import collections
import json
from pathlib import Path
import UnityPy

root = Path(__file__).resolve().parents[2]
out = Path(__file__).resolve().parent / 'inspection'
out.mkdir(parents=True, exist_ok=True)
paths = list((root / 'KingOfTheCastle_Data').glob('*.assets'))
paths += list((root / 'KingOfTheCastle_Data').glob('level*'))
paths += list((root / 'KingOfTheCastle_Data/StreamingAssets/aa/StandaloneWindows64').rglob('*.bundle'))
for path in paths:
    env = UnityPy.load(str(path))
    counts = collections.Counter(obj.type.name for obj in env.objects)
    samples, errors = [], collections.Counter()
    for obj in env.objects:
        if obj.type.name not in ('TextAsset', 'MonoBehaviour', 'Font'):
            continue
        try:
            tree = obj.parse_as_dict()
        except Exception as e:
            errors[type(e).__name__ + ': ' + str(e)[:100]] += 1
            continue
        samples.append({'id': obj.path_id, 'type': obj.type.name, 'tree': tree})
    (out / (path.name + '.json')).write_text(json.dumps(samples, ensure_ascii=False, indent=2), encoding='utf-8', errors='surrogateescape')
    print(path.name, dict(counts), 'errors=',dict(errors), flush=True)
