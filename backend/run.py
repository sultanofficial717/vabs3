import os
import sys
from pathlib import Path

# Add project root and backend to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    host = os.environ.get("HOST", "0.0.0.0")
    debug = os.environ.get("DEBUG", "true").lower() in ("true", "1", "yes")

    print("=" * 60)
    print("  AUTISM LENS CLINICAL DECISION SUPPORT SYSTEM")
    print(f"  Backend server running at: http://127.0.0.1:{port}")
    print("=" * 60)

    app.run(host=host, port=port, debug=debug)
