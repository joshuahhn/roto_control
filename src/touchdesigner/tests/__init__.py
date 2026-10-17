"""Keep runtime tests and shared fixtures importable from the source root."""
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parents[1]
for path in (SOURCE / 'tests', SOURCE / 'build', SOURCE / 'upgrade',
             SOURCE / 'verify', SOURCE / 'scripts', SOURCE / 'diagnostics/runtime',
             SOURCE / 'code/py/roto_python'):
    sys.path.insert(0, str(path))
