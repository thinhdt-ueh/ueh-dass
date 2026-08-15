"""Self-contained Windows launcher for DASS.

Starts the local Streamlit server (using the project's .venv) and opens the
default browser at http://localhost:8501 once the server is ready. Meant to
be compiled to DASS.exe with PyInstaller and kept in the project's root
folder (next to app.py and .venv), since it locates them by relative path.
"""

import os
import subprocess
import sys
import time
import urllib.request
import webbrowser

HOST = "127.0.0.1"
PORT = "8501"
URL = f"http://{HOST}:{PORT}"


def base_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def find_streamlit(root: str) -> list[str]:
    venv_streamlit = os.path.join(root, ".venv", "Scripts", "streamlit.exe")
    if os.path.isfile(venv_streamlit):
        return [venv_streamlit]
    venv_python = os.path.join(root, ".venv", "Scripts", "python.exe")
    if os.path.isfile(venv_python):
        return [venv_python, "-m", "streamlit"]
    return ["streamlit"]


def wait_for_server(url: str, timeout: float = 60.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2):
                return True
        except Exception:
            time.sleep(1)
    return False


def log(msg: str) -> None:
    print(msg, flush=True)


def main() -> int:
    root = base_dir()
    app_path = os.path.join(root, "app.py")

    if not os.path.isfile(app_path):
        log(f"[DASS] Khong tim thay app.py tai: {app_path}")
        log("[DASS] File DASS.exe phai nam trong thu muc goc cua du an (cung cap voi app.py va .venv).")
        input("Nhan Enter de thoat...")
        return 1

    cmd = find_streamlit(root) + [
        "run",
        app_path,
        f"--server.port={PORT}",
        f"--server.address={HOST}",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
    ]

    log("[DASS] Dang khoi dong may chu ung dung...")
    proc = subprocess.Popen(cmd, cwd=root)

    log("[DASS] Dang cho may chu san sang...")
    if wait_for_server(URL):
        log(f"[DASS] San sang! Dang mo trinh duyet tai {URL}")
        webbrowser.open(URL)
    else:
        log("[DASS] May chu chua phan hoi sau 60 giay, van thu mo trinh duyet...")
        webbrowser.open(URL)

    log("[DASS] Dong cua so nay (hoac nhan Ctrl+C) de dung ung dung.")
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
    return proc.returncode or 0


if __name__ == "__main__":
    sys.exit(main())
