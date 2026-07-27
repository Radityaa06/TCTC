import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
SCREENSHOT_DIR = BASE_DIR / "screenshots"

for d in [DATA_DIR, LOG_DIR, SCREENSHOT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

TARGET_URL = "https://quiz.toitctc.com/"
EXCEL_FILE_PATH = DATA_DIR / "students.xlsx"
FAILED_EXCEL_PATH = DATA_DIR / "failed_students.xlsx"
PROGRESS_STATE_FILE = DATA_DIR / ".progress_state.json"

# Auto-detect Cloud Linux (Render) vs Local Mac
IS_CLOUD = sys.platform.startswith("linux") or os.environ.get("RENDER") is not None
HEADLESS = True if IS_CLOUD else os.environ.get("HEADLESS", "false").lower() == "true"

BROWSER_TIMEOUT_MS = 45000
MAX_RETRIES = 3
RETRY_DELAY_SEC = 2

ENABLE_QUIZ_SOLVER = True
QUIZ_ANSWER_STRATEGY = "random"
MIN_THINK_TIME_SEC = 1.5
MAX_THINK_TIME_SEC = 3.5
QUIZ_TIMEOUT_SEC = 30
