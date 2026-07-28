import asyncio
import os
import sys
from pathlib import Path
import glob

# Ensure server module is in path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR / "server"))

from automation_engine import run_automation_task
from config import TARGET_URL

async def main():
    print("==================================================")
    print("   🚀 AUTO-FORM-PLATFORM LOCAL EXECUTION ENGINE   ")
    print("==================================================")
    print("The robot will now open Google Chrome and execute")
    print("the automation live on your computer. Please do")
    print("not touch the mouse while the bot is typing.")
    print("==================================================\n")

    # Find the latest uploaded dataset in server/temp or use default
    temp_dir = BASE_DIR / "server" / "temp"
    uploaded_files = glob.glob(str(temp_dir / "uploaded_*.xlsx")) + glob.glob(str(temp_dir / "uploaded_*.csv"))
    
    if uploaded_files:
        # Get the most recently uploaded file
        latest_file = max(uploaded_files, key=os.path.getmtime)
        print(f"[SYSTEM] Using recently uploaded dataset: {Path(latest_file).name}")
        file_path = latest_file
    else:
        file_path = str(BASE_DIR / "server" / "data" / "students.xlsx")
        print(f"[SYSTEM] Using default dataset: data/students.xlsx")

    # Dummy state object for compatibility with run_automation_task
    state = {
        "is_running": False,
        "is_paused": False,
        "progress": {"completed": 0, "failed": 0, "total": 0},
        "logs": []
    }

    try:
        await run_automation_task(TARGET_URL, file_path, state)
    except KeyboardInterrupt:
        print("\n[SYSTEM] Local Execution Engine Terminated by User.")
    except Exception as e:
        print(f"\n[CRITICAL ERROR] {e}")

if __name__ == "__main__":
    asyncio.run(main())
