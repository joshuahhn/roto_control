"""Runtime test discovery from the TouchDesigner source root."""
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parents[1]
for path in (SOURCE / 'tests/runtime', SOURCE / 'scripts',
             SOURCE / 'diagnostics/runtime', SOURCE / 'code/py/roto_python'):
    sys.path.insert(0, str(path))
