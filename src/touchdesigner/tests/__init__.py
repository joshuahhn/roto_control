"""Keep shared test fixtures importable during recursive unittest discovery."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))
