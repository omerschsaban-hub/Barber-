from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_URL = "http://127.0.0.1:8000"


def healthy(url: str) -> bool:
    try:
        with urlopen(f"{url.rstrip('/')}/health", timeout=2) as response:
            return response.status == 200
    except (OSError, URLError):
        return False


def main() -> int:
    configured_url = os.environ.get("FABRIENT_ENGINE_URL", "").strip().rstrip("/")
    url = configured_url or DEFAULT_URL
    child: subprocess.Popen[bytes] | None = None

    if not healthy(url):
        if configured_url:
            print(f"Configured engineering API is not healthy: {url}", file=sys.stderr)
            return 2
        env = os.environ.copy()
        env.update({
            "FABRIENT_ENGINE_URL": DEFAULT_URL,
            "FLYWHEEL_ENABLE_PRODUCTION": "false",
            "FLYWHEEL_SCHEDULER_ENABLED": "false",
        })
        child = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "services.engine.main:app", "--host", "127.0.0.1", "--port", "8000"],
            cwd=ROOT,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline and not healthy(DEFAULT_URL):
            if child.poll() is not None:
                details = child.stderr.read().decode(errors="replace") if child.stderr else ""
                print(f"Local engineering API exited before becoming healthy.\n{details}", file=sys.stderr)
                return child.returncode or 1
            time.sleep(0.25)
        if not healthy(DEFAULT_URL):
            child.terminate()
            print("Local engineering API did not become healthy within 45 seconds.", file=sys.stderr)
            return 1
        url = DEFAULT_URL

    env = os.environ.copy()
    env["FABRIENT_ENGINE_URL"] = url
    try:
        return subprocess.call([sys.executable, "-m", "pytest", "-q", "tests/mcp"], cwd=ROOT, env=env)
    finally:
        if child is not None and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()


if __name__ == "__main__":
    raise SystemExit(main())
