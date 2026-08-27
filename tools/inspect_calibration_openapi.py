import json
from pathlib import Path

spec = json.loads(Path('/tmp/fabrient-openapi.json').read_text())
for path in ('/v1/calibrate', '/v1/toolbox/calibrate_from_observations'):
    print(f'PATH {path}')
    print(json.dumps(spec.get('paths', {}).get(path), indent=2))
print('SCHEMAS')
for name in ('CalibrationInput', 'CalibrationRequest', 'Observation'):
    if name in spec.get('components', {}).get('schemas', {}):
        print(name)
        print(json.dumps(spec['components']['schemas'][name], indent=2))
