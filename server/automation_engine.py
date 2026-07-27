import asyncio
import time
from pathlib import Path
from typing import Dict, Any
import pandas as pd

import sys
REG_BOT_DIR = Path(__file__).resolve().parent
if str(REG_BOT_DIR) not in sys.path:
    sys.path.append(str(REG_BOT_DIR))

try:
    from registration_bot import RegistrationBot
    from config import HEADLESS
except Exception as err:
    RegistrationBot = None
    HEADLESS = True
    print(f"Import error: {err}")


def run_batch_sync(url: str, file_path: str, state: Dict[str, Any]):
    """
    Synchronous worker running on a dedicated thread with Pause / Resume & Headless Cloud support!
    """
    def send_log(msg: str):
        print(f"[BOT] {msg}")
        log_entry = {
            "log": msg,
            "metrics": {
                "completed": state["progress"]["completed"],
                "failed": state["progress"]["failed"],
                "total": state["progress"]["total"]
            }
        }
        state["logs"].append(log_entry)

    send_log(f"[INIT] Launching Playwright Chrome browser for {url} (Headless: {HEADLESS})...")

    if not file_path or not Path(file_path).exists():
        file_path = str(REG_BOT_DIR / "data" / "students.xlsx")
        send_log(f"[DATASET] Using default dataset: {file_path}")
    else:
        send_log(f"[DATASET] Using uploaded external user file: {file_path}")

    try:
        df = pd.read_excel(file_path, dtype=str) if not file_path.endswith(".csv") else pd.read_csv(file_path, dtype=str)
        total = len(df)
        state["progress"]["total"] = total
        state["progress"]["completed"] = 0
        state["progress"]["failed"] = 0

        send_log(f"[DATASET] Loaded {total} candidate records. Starting batch automation...")

        if RegistrationBot:
            bot = RegistrationBot(url=url, headless=HEADLESS)
            bot.start()

            for idx, row in df.iterrows():
                # Check for Pause state trigger
                while state.get("is_paused", False):
                    time.sleep(0.5)

                student = row.to_dict()
                student["_row_index"] = idx + 1
                student_name = student.get("Name") or student.get("Student Name") or student.get("Full Name") or f"Student #{idx+1}"
                email = student.get("Guardian Email") or student.get("Email") or student.get("Email Address") or ""

                send_log(f"[{idx+1}/{total}] Processing Candidate: {student_name} ({email})...")

                success, msg = bot.process_student_registration(student, idx + 1, total)

                if success:
                    state["progress"]["completed"] += 1
                    send_log(f"  ✓ Success: {student_name} - {msg}")
                else:
                    state["progress"]["failed"] += 1
                    send_log(f"  ✗ Failed: {student_name} - {msg}")

                time.sleep(0.5)

            bot.stop()
        else:
            send_log("[ERROR] RegistrationBot module failed to initialize.")

        send_log(f"[COMPLETED] Batch processing finished! {state['progress']['completed']}/{total} candidates successfully completed.")

    except Exception as e:
        send_log(f"[CRITICAL ERROR] Automation failed: {e}")
    finally:
        state["is_running"] = False
        state["is_paused"] = False


async def run_automation_task(url: str, file_path: str, state: Dict[str, Any]):
    state["is_running"] = True
    state["is_paused"] = False
    await asyncio.to_thread(run_batch_sync, url, file_path, state)
