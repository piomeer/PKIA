import os
import json
import logging
from datetime import datetime, timezone

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from filelock import FileLock

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="PKIA Storage Adapter", version="1.0.0")

DATA_FILE = os.getenv("PKIA_STORAGE_PATH", os.path.join(os.getcwd(), "pkia_project", "pkia_storage.jsonl"))
LOCK_FILE = DATA_FILE + ".lock"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_analysis(raw: dict) -> dict:
    return {
        "classification": raw.get("classification"),
        "scores": {
            "career_alignment": raw.get("career_alignment"),
            "interest_match": raw.get("interest_match"),
            "trend_score": raw.get("trend_score"),
            "research_score": raw.get("research_score"),
        },
        "total_score": raw.get("total_score"),
        "recommendation": raw.get("recommendation"),
        "reasoning": raw.get("reasoning"),
        "tags": raw.get("tags", []),
        "confidence": raw.get("confidence"),
    }


@app.post("/api/v1/projects")
async def receive_project(request: Request):
    body = await request.json()
    batch_id = body.get("batch_id", "unknown")
    project_data = body.get("project_data", body)

    analysis_raw = body.get("analysis") or body.get("analysis_result")
    has_analysis = analysis_raw is not None

    os.makedirs(os.path.dirname(DATA_FILE) or ".", exist_ok=True)
    record = {
        "batch_id": batch_id,
        "project_data": project_data,
        "pipeline_status": "ANALYZED" if has_analysis else body.get("pipeline_status", "PROMOTED"),
    }
    if has_analysis:
        record["analysis"] = _normalize_analysis(analysis_raw)
        record["updated_at"] = _now()

    with FileLock(LOCK_FILE):
        with open(DATA_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    if has_analysis:
        logger.info(f"Project stored: {project_data.get('project_name', '?')} (batch={batch_id}, analysis=yes)")
    else:
        logger.info(f"Project stored: {project_data.get('project_name', '?')} (batch={batch_id})")
    return JSONResponse({"status": "ok", "stored": True}, status_code=200)


@app.patch("/api/v1/projects/{project_id}/analysis")
async def patch_analysis(project_id: str, request: Request):
    body = await request.json()

    if not os.path.exists(DATA_FILE):
        return JSONResponse({"error": "No data file found"}, status_code=404)

    with FileLock(LOCK_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()

        found = False
        updated_lines = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            record = json.loads(stripped)
            pd = record.get("project_data", {})
            if pd.get("project_id") == project_id:
                record["analysis"] = {
                    "classification": body.get("classification"),
                    "scores": {
                        "career_alignment": body.get("career_alignment"),
                        "interest_match": body.get("interest_match"),
                        "trend_score": body.get("trend_score"),
                        "research_score": body.get("research_score"),
                    },
                    "total_score": body.get("total_score"),
                    "recommendation": body.get("recommendation"),
                    "reasoning": body.get("reasoning"),
                    "tags": body.get("tags", []),
                    "confidence": body.get("confidence"),
                }
                record["pipeline_status"] = "ANALYZED"
                record["updated_at"] = _now()
                found = True

            updated_lines.append(json.dumps(record, ensure_ascii=False) + "\n")

        if not found:
            return JSONResponse(
                {"error": f"project_id '{project_id}' not found in storage"},
                status_code=404,
            )

        with open(DATA_FILE, "w", encoding="utf-8") as f:
            f.writelines(updated_lines)

    logger.info(f"Analysis patched for project_id={project_id}")
    return JSONResponse({"status": "ok", "patched": True, "project_id": project_id}, status_code=200)


@app.get("/health")
async def health():
    return {"status": "ok", "storage_path": DATA_FILE}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("ADAPTER_PORT", "8000")))
