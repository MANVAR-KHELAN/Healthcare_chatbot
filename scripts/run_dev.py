import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
