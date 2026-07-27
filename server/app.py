import os
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List
from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
import pandas as pd

from form_inspector import inspect_target_form
from template_builder import generate_excel_template

BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "temp"
TEMP_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Universal Web Automation Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global State Container
state = {
    "current_url": "https://quiz.toitctc.com/",
    "fields": [],
    "template_file": None,
    "uploaded_file": None,
    "columns": [],
    "total_rows": 0,
    "is_running": False,
    "is_paused": False,
    "progress": {"completed": 0, "failed": 0, "total": 0},
    "logs": [
        {"log": "[SYSTEM] Universal Web Automation Dashboard Ready.", "metrics": {"completed": 0, "failed": 0, "total": 0}},
        {"log": "[SYSTEM] Target Web App: https://quiz.toitctc.com/", "metrics": {"completed": 0, "failed": 0, "total": 0}},
        {"log": "[SYSTEM] Awaiting user trigger...", "metrics": {"completed": 0, "failed": 0, "total": 0}}
    ]
}


@app.post("/api/inspect")
async def inspect_url(data: Dict[str, str]):
    url = data.get("url", "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="Target URL is required.")

    state["current_url"] = url
    result = await inspect_target_form(url)

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to inspect URL."))

    state["fields"] = result.get("fields", [])
    template_path = TEMP_DIR / "generated_template.xlsx"
    generate_excel_template(state["fields"], template_path)
    state["template_file"] = str(template_path)

    return {
        "status": "success",
        "url": url,
        "title": result.get("title"),
        "fields": state["fields"],
        "template_available": True
    }


@app.get("/api/download-template")
async def download_template():
    if not state["template_file"] or not Path(state["template_file"]).exists():
        default_fields = [
            {"label": "Name", "type": "text"},
            {"label": "Class", "type": "text"},
            {"label": "School", "type": "text"},
            {"label": "Parent's Name", "type": "text"},
            {"label": "Phone Number", "type": "text"},
            {"label": "Home Address", "type": "text"},
            {"label": "Pin Code", "type": "text"},
            {"label": "City", "type": "text"},
            {"label": "State", "type": "text"},
            {"label": "Guardian Email", "type": "email"},
            {"label": "Password", "type": "password"},
            {"label": "Confirm Password", "type": "password"}
        ]
        template_path = TEMP_DIR / "generated_template.xlsx"
        generate_excel_template(default_fields, template_path)
        state["template_file"] = str(template_path)

    return FileResponse(
        state["template_file"],
        filename="student_registration_template.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith((".xlsx", ".xls", ".csv")):
        raise HTTPException(status_code=400, detail="Only Excel (.xlsx, .xls) or CSV files are supported.")

    file_path = TEMP_DIR / f"uploaded_{file.filename}"
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    state["uploaded_file"] = str(file_path)

    try:
        if file.filename.endswith(".csv"):
            df = pd.read_csv(file_path, dtype=str)
        else:
            df = pd.read_excel(file_path, dtype=str)

        columns = list(df.columns)
        state["columns"] = columns
        state["total_rows"] = len(df)
        preview = df.head(3).to_dict(orient="records")

        return {
            "status": "success",
            "filename": file.filename,
            "columns": columns,
            "total_rows": len(df),
            "preview": preview
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse dataset: {e}")


@app.get("/api/stream")
async def event_stream():
    """SSE Real-time log & progress event stream for live dashboard updates."""
    async def log_generator():
        last_index = 0
        while True:
            current_logs = state["logs"]
            if last_index < len(current_logs):
                for item in current_logs[last_index:]:
                    yield f"data: {json.dumps(item)}\n\n"
                last_index = len(current_logs)
            await asyncio.sleep(0.3)

    return StreamingResponse(log_generator(), media_type="text/event-stream")


@app.post("/api/start")
async def start_automation(background_tasks: BackgroundTasks):
    if state["is_running"]:
        raise HTTPException(status_code=400, detail="Automation is already running.")

    from automation_engine import run_automation_task

    state["is_paused"] = False
    state["progress"]["completed"] = 0
    state["progress"]["failed"] = 0
    state["progress"]["total"] = state["total_rows"] or 250
    state["logs"] = [
        {"log": "[START] Triggering Playwright batch automation & MCQ quiz solver...", "metrics": state["progress"]}
    ]

    background_tasks.add_task(
        run_automation_task,
        state["current_url"],
        state["uploaded_file"],
        state
    )

    return {
        "status": "started",
        "url": state["current_url"],
        "total_rows": state["progress"]["total"]
    }


@app.post("/api/pause")
async def pause_automation():
    if not state["is_running"]:
        raise HTTPException(status_code=400, detail="Automation is not running.")

    state["is_paused"] = True
    state["logs"].append({
        "log": "[PAUSE] Automation execution paused by user.",
        "metrics": state["progress"]
    })
    return {"status": "paused"}


@app.post("/api/resume")
async def resume_automation():
    if not state["is_running"]:
        raise HTTPException(status_code=400, detail="Automation is not running.")

    state["is_paused"] = False
    state["logs"].append({
        "log": "[RESUME] Automation execution resumed.",
        "metrics": state["progress"]
    })
    return {"status": "resumed"}


@app.get("/api/status")
async def get_status():
    return {
        "current_url": state["current_url"],
        "is_running": state["is_running"],
        "is_paused": state["is_paused"],
        "progress": state["progress"],
        "total_rows": state["total_rows"],
        "fields_count": len(state["fields"])
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
