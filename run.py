#!/usr/bin/env python3
"""
PKIA Unified Entry Point — run.py

Usage:
    python run.py                          # Full startup
    python run.py --skip-docker-check      # Skip Docker verification
    python run.py --adapter-port=9000      # Custom Storage Adapter port
    python run.py --output-dir=/tmp/reports  # Custom report output directory

Flow:
    1. Check Docker running (optional)
    2. Check Dify API reachable
    3. Start Storage Adapter (uvicorn)
    4. Run Collector + Dify Runner
    5. Generate Daily Report (Markdown)
    6. Print execution summary
"""

import os
import sys
import time
import signal
import logging
import subprocess
import argparse
from pathlib import Path

import requests
from dotenv import load_dotenv

from pkia_reporter.reporter import load_json, generate_report, write_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("pkia.runner")

load_dotenv()

DIFY_API_KEY = os.getenv("DIFY_API_KEY", "")
DIFY_API_BASE_URL = os.getenv("DIFY_API_BASE_URL", os.getenv("DIFY_API_URL", "http://127.0.0.1/v1"))
STORAGE_ADAPTER_PORT = int(os.getenv("ADAPTER_PORT", "8000"))
REPORTS_DIR = os.getenv("PKIA_REPORTS_DIR", os.path.join(os.getcwd(), "pkia", "reports"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PKIA Unified Startup Entry Point")
    parser.add_argument("--skip-docker-check", action="store_true", help="Skip Docker daemon check")
    parser.add_argument("--adapter-port", type=int, default=STORAGE_ADAPTER_PORT, help="Storage Adapter port")
    parser.add_argument("--output-dir", type=str, default=REPORTS_DIR, help="Report output directory")
    return parser.parse_args()


def check_docker() -> bool:
    logger.info("Step 1/4 — Checking Docker daemon ...")
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            logger.info("  ✅ Docker is running")
            return True
        logger.error(f"  ❌ Docker not reachable: {result.stderr.strip()}")
        return False
    except FileNotFoundError:
        logger.error("  ❌ docker command not found")
        return False
    except subprocess.TimeoutExpired:
        logger.error("  ❌ docker info timed out")
        return False


def check_dify_api(base_url: str) -> bool:
    logger.info("Step 2/4 — Checking Dify API reachability ...")
    if not DIFY_API_KEY:
        logger.warning("  ⚠️  DIFY_API_KEY not set, skipping health check")
        return True
    try:
        url = f"{base_url.rstrip('/v1')}/v1/workflows/run"
        headers = {"Authorization": f"Bearer {DIFY_API_KEY}"}
        resp = requests.get(url.replace("/run", ""), headers=headers, timeout=10)
        if resp.status_code < 500:
            logger.info(f"  ✅ Dify API reachable at {base_url}")
            return True
        logger.error(f"  ❌ Dify returned {resp.status_code}: {resp.text[:200]}")
        return False
    except requests.ConnectionError:
        logger.error(f"  ❌ Cannot connect to {base_url}")
        return False
    except requests.Timeout:
        logger.error(f"  ❌ Connection to {base_url} timed out")
        return False


def start_storage_adapter(port: int) -> subprocess.Popen | None:
    logger.info("Step 3/4 — Starting Storage Adapter ...")
    try:
        proc = subprocess.Popen(
            [
                sys.executable, "-m", "uvicorn",
                "pkia_project.storage_adapter:app",
                "--host", "0.0.0.0",
                "--port", str(port),
                "--log-level", "warning",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        time.sleep(2)
        if proc.poll() is not None:
            logger.error(f"  ❌ Storage Adapter exited prematurely (code {proc.returncode})")
            return None
        # Verify it's listening
        try:
            resp = requests.get(f"http://127.0.0.1:{port}/health", timeout=5)
            if resp.status_code == 200:
                logger.info(f"  ✅ Storage Adapter listening on port {port}")
                return proc
        except requests.ConnectionError:
            logger.error("  ❌ Storage Adapter started but not responding")
            proc.kill()
            return None
    except FileNotFoundError:
        logger.error("  ❌ uvicorn not found — install with: pip install uvicorn")
        return None


def run_collector(output_dir: str) -> dict:
    logger.info("Step 4/4 — Running Collector + Dify Runner ...")
    env = os.environ.copy()
    env["PKIA_REPORTS_DIR"] = output_dir
    env["ADAPTER_PORT"] = str(STORAGE_ADAPTER_PORT)

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pkia_collector.runner"],
            capture_output=True, text=True, timeout=600,
            env=env,
        )
        if result.stdout:
            for line in result.stdout.splitlines():
                logger.info(f"  {line}")
        if result.stderr:
            for line in result.stderr.splitlines():
                logger.warning(f"  {line}")

        # Parse summary from output
        projects_count = 0
        pushed = False
        for line in result.stdout.splitlines():
            if "共" in line and "个项目" in line:
                import re
                m = re.search(r"共\s*(\d+)\s*个项目", line)
                if m:
                    projects_count = int(m.group(1))
            if "成功触发" in line or "success" in line.lower():
                pushed = True

        return {
            "returncode": result.returncode,
            "projects_count": projects_count,
            "pushed": pushed,
            "success": result.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        logger.error("  ❌ Collector timed out after 600s")
        return {"returncode": -1, "projects_count": 0, "pushed": False, "success": False}


def run_reporter(storage_path: str, output_dir: str) -> dict:
    logger.info("Step 5/6 — Generating Daily Report ...")
    projects = load_json(storage_path)
    if not projects:
        logger.warning("  ⚠️  No data for report generation")
        return {"success": False, "path": None, "count": 0}

    report = generate_report(projects)
    path = write_report(report, output_dir)
    logger.info("  ✅ Report written: %s (%d projects)", path, len(projects))
    return {"success": True, "path": path, "count": len(projects)}


def print_summary(results: dict):
    print()
    print("=" * 50)
    print("  PKIA Run Summary")
    print("=" * 50)
    print(f"  Projects collected:  {results.get('projects_count', '?')}")
    print(f"  Pushed to Dify:      {'✅ Yes' if results.get('pushed') else '❌ No'}")
    print(f"  Report file:         {results.get('report_path', '?')}")
    status = "✅ SUCCESS" if results.get("success") else "❌ FAILED"
    print(f"  Overall status:      {status}")
    print("=" * 50)


def main():
    args = parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    # Step 1: Docker check
    if not args.skip_docker_check:
        if not check_docker():
            logger.error("Aborting — Docker is required. Use --skip-docker-check to bypass.")
            sys.exit(1)
    else:
        logger.info("Step 1/4 — Skipped (--skip-docker-check)")

    # Step 2: Dify API check
    base_url = DIFY_API_BASE_URL
    if not check_dify_api(base_url):
        logger.warning("Continuing without Dify API validation — may fail at push time.")

    # Step 3: Start Storage Adapter
    adapter_proc = start_storage_adapter(args.adapter_port)
    if adapter_proc is None:
        logger.warning("Continuing without Storage Adapter — report won't be persisted.")

    # Step 4: Run Collector
    results = run_collector(args.output_dir)
    results["output_dir"] = args.output_dir

    # Step 5: Generate Daily Report
    storage_path = os.path.join(os.getcwd(), "pkia_project", "pkia_storage.jsonl")
    report_result = run_reporter(storage_path, args.output_dir)
    results["report_path"] = report_result.get("path")

    # Step 6: Summary
    print_summary(results)

    # Cleanup
    if adapter_proc is not None:
        adapter_proc.terminate()
        try:
            adapter_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            adapter_proc.kill()

    if not results.get("success"):
        sys.exit(1)


def signal_handler(signum, frame):
    logger.info("Received signal %s, shutting down ...", signum)
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    main()
