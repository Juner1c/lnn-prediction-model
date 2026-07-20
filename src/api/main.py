import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from src.api.routes import router

app = FastAPI(
    title="Kloudtech Telemetry & LNN Heat Index Prediction API",
    version="1.0.0",
    description="REST microservice exposing Kloudtech telemetry endpoints and LNN/GNN Heat Index forecast capabilities."
)

app.include_router(router)

STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "static"))
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=FileResponse)
def serve_dashboard():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"status": "healthy", "service": "LNN Heat Index Microservice"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "LNN Heat Index Microservice", "version": "1.0.0"}

