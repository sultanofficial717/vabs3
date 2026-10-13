import os
import sys
import threading
import time
import webbrowser
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app import create_app

app = create_app()


def open_browser(url: str):
    time.sleep(1.2)
    try:
        webbrowser.open(url)
    except Exception:
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    host = os.environ.get("HOST", "0.0.0.0")
    debug = os.environ.get("DEBUG", "false").lower() in ("true", "1", "yes")

    app_url = f"http://127.0.0.1:{port}"

    print("=" * 65)
    print("  🩺 AUTISM LENS — CLINICAL DECISION SUPPORT SYSTEM")
    print(f"  🚀 Web Application running at: {app_url}")
    print("  Opening browser automatically...")
    print("  Press CTRL+C in this terminal to stop the server.")
    print("=" * 65)

    threading.Thread(target=open_browser, args=(app_url,), daemon=True).start()

    app.run(host=host, port=port, debug=debug)
