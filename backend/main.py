"""
AegisPath FastAPI Application Entrypoint.
Provides high-throughput REST APIs for enterprise graph management,
GNN attack path prediction, VM simulation, attention-based XAI, and counterfactual defense.
Directly serves production static UI build at `/` for live standalone hosting.
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.routes import (
    graphs_router,
    prediction_router,
    explain_router,
    defense_router,
    experiments_router,
    simulation_router,
    xai_router,
)

app = FastAPI(
    title="AegisPath API & Live Cyber Command Center",
    description="AI-Powered Enterprise Attack Path Prediction & Security Decision Support System",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Sub-Routers
app.include_router(graphs_router)
app.include_router(prediction_router)
app.include_router(explain_router)
app.include_router(defense_router)
app.include_router(experiments_router)
app.include_router(simulation_router)
app.include_router(xai_router)


@app.get("/health", tags=["Health"])
def health_check():
    """Service liveness probe."""
    return {"status": "healthy", "service": "aegispath-backend", "version": "0.2.0"}


# Serve static production frontend build if present
dist_dir = Path("frontend/dist")
if dist_dir.exists():
    app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="static_frontend")
else:
    @app.get("/", tags=["Health"])
    def root():
        return {
            "system": "AegisPath",
            "status": "online",
            "description": "AI-Powered Enterprise Attack Path Prediction and Decision Support System",
            "docs": "/docs",
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
