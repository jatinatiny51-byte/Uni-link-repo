import os
import sys
import subprocess
import time
import signal
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Any
import uvicorn


# ==========================================
# 0. MYSQL SERVICE STARTUP (WINDOWS)
# ==========================================
def start_mysql_service():
    """Start MySQL80 service on Windows automatically"""
    try:
        # Check if MySQL service is already running
        result = subprocess.run(
            ["sc", "query", "MySQL80"],
            capture_output=True,
            text=True
        )

        if "RUNNING" in result.stdout:
            print("✅ [STARTUP] MySQL service already running")
            return

        # Start the service
        print("🗄️  [STARTUP] Starting MySQL80 service...")
        subprocess.run(
            ["net", "start", "MySQL80"],
            capture_output=True,
            check=False
        )

        time.sleep(2)  # Wait for service to be ready
        print("✅ [STARTUP] MySQL80 service started successfully")

    except PermissionError:
        print("❌ [ERROR] Run this script as Administrator to start MySQL service")
        sys.exit(1)
    except Exception as e:
        print(f"⚠️  [WARNING] Could not start MySQL service: {e}")


def stop_mysql_service():
    """Stop MySQL80 service on Windows"""
    try:
        subprocess.run(
            ["net", "stop", "MySQL80"],
            capture_output=True,
            check=False
        )
    except:
        pass


# ==========================================
# 1. DYNAMIC PATH RESOLUTION
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
INDEX_HTML_PATH = os.path.join(FRONTEND_DIR, "index.html")

# Dynamically load the backend controllers
try:
    from App.ui.controller import UIController

    srm_controller = UIController()
except Exception as e:
    print(f"❌ [CRITICAL] Failed to load backend modules: {e}")
    sys.exit(1)


# ==========================================
# 2. SYSTEM LIFESPAN (IPC BOOTUP)
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "=" * 60)
    print("🚀 [SYSTEM] Booting SRM Academic Portal Gateway...")
    print(f"📂 [PATH] Frontend dynamically resolved to: {FRONTEND_DIR}")

    try:
        srm_controller.boot()
        print("✅ [SYSTEM] IPC Orchestrator Online. Server active at http://localhost:5000")
    except Exception as e:
        print(f"❌ [FATAL ERROR] Backend Modules failed to boot: {e}")

    print("=" * 60 + "\n")
    yield
    print("\n🛑 [SYSTEM] Shutting down connection pools and workers safely...")
    srm_controller.shutdown()
    stop_mysql_service()


app = FastAPI(lifespan=lifespan)


# ==========================================
# 3. STANDARD API GATEWAY (PURE)
# ==========================================
class APIRequest(BaseModel):
    action: str
    args: List[Any] = []


@app.post("/api")
def api_gateway(req: APIRequest):
    """Routes standard JSON signals to the backend IPC Orchestrator."""
    try:
        response = srm_controller.dispatch(req.action, *req.args)

        if not isinstance(response, dict) or "status" not in response:
            return {"status": "error", "message": "Backend format mismatch.", "payload": None}
        return response
    except Exception as e:
        return {"status": "error", "message": f"Gateway Error: {str(e)}", "payload": None}


# ==========================================
# 4. STATIC FILE SERVER & SPA ROUTING
# ==========================================
os.makedirs(FRONTEND_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
async def serve_root():
    """Main application entry point."""
    if not os.path.exists(INDEX_HTML_PATH):
        return JSONResponse({"error": f"Missing frontend/index.html at: {INDEX_HTML_PATH}"}, status_code=404)
    return FileResponse(INDEX_HTML_PATH)


@app.get("/{catchall:path}")
async def serve_spa(catchall: str):
    """SPA Catch-all: Ensures direct URLs map correctly to index.html."""
    if not os.path.exists(INDEX_HTML_PATH):
        return JSONResponse({"error": "frontend/index.html is missing."}, status_code=404)
    return FileResponse(INDEX_HTML_PATH)


if __name__ == "__main__":
    # Start MySQL service before the server
    start_mysql_service()

    # Run the server
    uvicorn.run("server:app", host="0.0.0.0", port=5000, reload=False, workers=1)