import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parent
UI_URL = "http://127.0.0.1:8000/static/index.html"
SCREENSHOT_PATH = PROJECT_ROOT / "ui_screenshot.jpg"
README_PATH = PROJECT_ROOT / "README.md"


def _is_server_ready(timeout_s: float = 0.8) -> bool:
    try:
        urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=timeout_s).read()
        return True
    except Exception:
        return False


def _start_server_if_needed() -> subprocess.Popen | None:
    if _is_server_ready():
        return None

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    deadline = time.time() + 60
    while time.time() < deadline:
        if proc.poll() is not None:
            out = proc.stdout.read() if proc.stdout else ""
            raise RuntimeError(f"Server failed to start.\n\n{out}")
        if _is_server_ready():
            return proc
        time.sleep(0.25)

    out = ""
    try:
        if proc.stdout:
            out = proc.stdout.read()
    except Exception:
        pass
    proc.terminate()
    raise TimeoutError(f"Timed out waiting for the server to start on http://127.0.0.1:8000\n\n{out}")


def _capture_screenshot() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        page.goto(UI_URL, wait_until="networkidle")
        page.wait_for_timeout(3000)
        page.screenshot(path=str(SCREENSHOT_PATH), type="jpeg", quality=88, full_page=False)
        browser.close()


def _update_readme() -> None:
    if not README_PATH.exists():
        raise FileNotFoundError(f"README.md not found at {README_PATH}")

    text = README_PATH.read_text(encoding="utf-8")
    text = re.sub(r"!\[[^\]]*\]\(\s*\.?/ui_screenshot\.jpg\s*\)", "![Project UI Preview](./ui_screenshot.jpg)", text)
    if "![Project UI Preview](./ui_screenshot.jpg)" not in text:
        text += "\n\n![Project UI Preview](./ui_screenshot.jpg)\n"
    README_PATH.write_text(text, encoding="utf-8")


def _git(*args: str) -> None:
    subprocess.run(["git", *args], cwd=str(PROJECT_ROOT), check=True)


def _git_commit_push() -> None:
    _git("add", "capture_ui.py", "README.md", "ui_screenshot.jpg")
    _git("commit", "-m", "chore: add UI screenshot")
    _git("push")


def main() -> None:
    server_proc = None
    try:
        server_proc = _start_server_if_needed()
        _capture_screenshot()
        _update_readme()
        _git_commit_push()
        print(f"Saved screenshot to: {SCREENSHOT_PATH}")
    finally:
        if server_proc is not None and server_proc.poll() is None:
            server_proc.terminate()


if __name__ == "__main__":
    main()
