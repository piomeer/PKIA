import os
import logging
from datetime import datetime

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="PKIA Storage Adapter", version="1.0.0")

REPORTS_DIR = os.getenv("PKIA_REPORTS_DIR", os.path.join(os.getcwd(), "pkia", "reports"))


@app.post("/report")
async def receive_report(request: Request):
    body = await request.body()
    content = body.decode("utf-8")

    date_str = request.headers.get("X-Date") or datetime.now().strftime("%Y-%m-%d")
    os.makedirs(REPORTS_DIR, exist_ok=True)
    path = os.path.join(REPORTS_DIR, f"{date_str}.md")

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"Report saved to {path} ({len(content)} bytes)")
    return JSONResponse({"status": "ok", "path": path}, status_code=200)


@app.get("/health")
async def health():
    return {"status": "ok", "reports_dir": REPORTS_DIR}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("ADAPTER_PORT", "8000")))
