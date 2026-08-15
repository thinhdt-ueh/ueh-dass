"""Self-contained Windows launcher for DASS.

Starts the local Streamlit server and opens the default browser at
http://localhost:8501 once ready. Meant to be compiled to DASS.exe with
PyInstaller and kept in the project's root folder (next to app.py), since
it locates the app by relative path.

Portability: the exe does NOT depend on a pre-existing .venv (venvs bake in
machine-specific paths and are not portable). On first run on any machine,
if no working .venv is found next to the exe, one is created automatically
from whatever system Python is available, and dependencies are installed
from requirements.txt. Subsequent runs reuse that venv and start instantly.
"""

import os
import shutil
import subprocess
import sys
import time
import urllib.request
import webbrowser

HOST = "127.0.0.1"
PORT = "8501"
URL = f"http://{HOST}:{PORT}"


def log(msg: str) -> None:
    print(msg, flush=True)


def base_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def find_system_python() -> list[str] | None:
    # Prefer the Windows "py" launcher (installed by python.org, finds Python
    # reliably even when it's not on PATH), then fall back to python3/python.
    py_launcher = shutil.which("py")
    if py_launcher:
        return [py_launcher, "-3"]
    for name in ("python3", "python"):
        exe = shutil.which(name)
        if exe:
            return [exe]
    return None


def venv_python_path(venv_dir: str) -> str:
    return os.path.join(venv_dir, "Scripts", "python.exe")


def venv_is_usable(venv_dir: str) -> bool:
    py = venv_python_path(venv_dir)
    if not os.path.isfile(py):
        return False
    try:
        result = subprocess.run(
            [py, "-c", "import streamlit"],
            cwd=venv_dir,
            capture_output=True,
            timeout=15,
        )
        return result.returncode == 0
    except Exception:
        return False


def ensure_venv(root: str) -> str:
    """Return path to a working venv python.exe, creating/installing it if needed."""
    venv_dir = os.path.join(root, ".venv")

    if venv_is_usable(venv_dir):
        return venv_python_path(venv_dir)

    log("[DASS] Chua co moi truong Python san sang, dang thiet lap lan dau (chi chay 1 lan)...")

    system_python = find_system_python()
    if system_python is None:
        log("[DASS] LOI: Khong tim thay Python tren may nay.")
        log("[DASS] Vui long cai Python 3.10+ tu https://www.python.org/downloads/ (nho tick 'Add python.exe to PATH'), roi chay lai DASS.exe.")
        input("Nhan Enter de thoat...")
        sys.exit(1)

    if not os.path.isdir(venv_dir):
        log("[DASS] Dang tao moi truong Python rieng (.venv)...")
        subprocess.run(system_python + ["-m", "venv", venv_dir], cwd=root, check=True)

    venv_py = venv_python_path(venv_dir)
    requirements = os.path.join(root, "requirements.txt")

    log("[DASS] Dang cai dat thu vien can thiet (co the mat vai phut trong lan dau)...")
    subprocess.run([venv_py, "-m", "pip", "install", "--upgrade", "pip"], cwd=root, check=True)
    subprocess.run([venv_py, "-m", "pip", "install", "-r", requirements], cwd=root, check=True)

    if not venv_is_usable(venv_dir):
        log("[DASS] LOI: Cai dat thu vien khong thanh cong. Vui long kiem tra ket noi Internet roi thu lai.")
        input("Nhan Enter de thoat...")
        sys.exit(1)

    log("[DASS] Thiet lap xong.")
    return venv_py


def wait_for_server(url: str, timeout: float = 60.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2):
                return True
        except Exception:
            time.sleep(1)
    return False


def main() -> int:
    root = base_dir()
    app_path = os.path.join(root, "app.py")

    if not os.path.isfile(app_path):
        log(f"[DASS] Khong tim thay app.py tai: {app_path}")
        log("[DASS] File DASS.exe phai nam trong thu muc goc cua du an (cung cap voi app.py, requirements.txt, ...).")
        input("Nhan Enter de thoat...")
        return 1

    venv_py = ensure_venv(root)

    cmd = [
        venv_py,
        "-m",
        "streamlit",
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
