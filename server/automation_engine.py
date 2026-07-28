import asyncio
import time
from pathlib import Path
from typing import Dict, Any
import pandas as pd
from playwright.async_api import async_playwright

import sys
REG_BOT_DIR = Path(__file__).resolve().parent
if str(REG_BOT_DIR) not in sys.path:
    sys.path.append(str(REG_BOT_DIR))

try:
    from registration_bot import process_student_registration
    from config import HEADLESS
    from logger import set_global_state_ref
except Exception as err:
    process_student_registration = None
    HEADLESS = True
    set_global_state_ref = lambda s: None
    print(f"Import error: {err}")


async def run_automation_task(url: str, file_path: str, state: Dict[str, Any]):
    """
    Fully Async Playwright Task Engine.
    Streams ALL internal Playwright logs live to the web UI console!
    """
    state["is_running"] = True
    state["is_paused"] = False

    set_global_state_ref(state)

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

    send_log(f"[INIT] Launching Async Playwright Chrome browser for {url} (Headless: {HEADLESS})...")

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

        async with async_playwright() as p:
            launch_args = [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage"
            ]

            browser = await p.chromium.launch(
                headless=HEADLESS,
                args=launch_args
            )

            for idx, row in df.iterrows():
                # Pause state check loop
                while state.get("is_paused", False):
                    await asyncio.sleep(0.5)

                student = row.to_dict()
                student["_row_index"] = idx + 1
                student_name = student.get("Name") or student.get("Student Name") or student.get("Full Name") or f"Student #{idx+1}"
                email = student.get("Guardian Email") or student.get("Email") or student.get("Email Address") or ""

                send_log(f"[{idx+1}/{total}] Processing Candidate: {student_name} ({email})...")

                # Fresh isolated context per candidate student
                context = await browser.new_context(
                    viewport={"width": 1280, "height": 800},
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
                )
                page = await context.new_page()
                await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

                try:
                    success, msg = await process_student_registration(page, student, idx + 1, total, url)
                    if success:
                        state["progress"]["completed"] += 1
                        send_log(f"  ✓ Success: {student_name} - {msg}")
                    else:
                        state["progress"]["failed"] += 1
                        send_log(f"  ✗ Failed: {student_name} - {msg}")
                except Exception as student_err:
                    state["progress"]["failed"] += 1
                    send_log(f"  ✗ Failed: {student_name} - {student_err}")
                finally:
                    await context.close()

                await asyncio.sleep(0.5)

            await browser.close()

        send_log(f"[COMPLETED] Batch processing finished! {state['progress']['completed']}/{total} candidates successfully completed.")

    except Exception as e:
        send_log(f"[CRITICAL ERROR] Automation failed: {e}")
    finally:
        state["is_running"] = False
        state["is_paused"] = False
