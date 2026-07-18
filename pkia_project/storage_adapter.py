import os
import json
import logging

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="PKIA Storage Adapter", version="1.0.0")

DATA_FILE = os.getenv("PKIA_STORAGE_PATH", os.path.join(os.getcwd(), "pkia_project", "pkia_storage.jsonl"))


@app.post("/api/v1/projects")
async def receive_project(request: Request):
    body = await request.json()
    batch_id = body.get("batch_id", "unknown")
    project_data = body.get("project_data", body)

    os.makedirs(os.path.dirname(DATA_FILE) or ".", exist_ok=True)
    record = {
        "batch_id": batch_id,
        "project_data": project_data,
        "pipeline_status": body.get("pipeline_status", "PROMOTED"),
    }
    with open(DATA_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    logger.info(f"Project stored: {project_data.get('project_name', '?')} (batch={batch_id})")
    return JSONResponse({"status": "ok", "stored": True}, status_code=200)


@app.get("/health")
async def health():
    return {"status": "ok", "storage_path": DATA_FILE}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("ADAPTER_PORT", "8000")))
