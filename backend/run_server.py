"""Start the Mini-Courier Planner (API + pre-built UI) with one command.

    python run_server.py [--port 8000] [--host 127.0.0.1] [--no-browser]
"""

from __future__ import annotations

import argparse
import threading
import time
import webbrowser

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="Mini-Courier Planner server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-browser", action="store_true", help="do not open the browser automatically")
    args = parser.parse_args()
    url = f"http://{args.host}:{args.port}"
    if not args.no_browser:
        threading.Thread(target=lambda: (time.sleep(1.5), webbrowser.open(url)), daemon=True).start()
    print(f"Mini-Courier Planner running at {url}  (Ctrl+C to stop)")
    uvicorn.run("app.main:app", host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
