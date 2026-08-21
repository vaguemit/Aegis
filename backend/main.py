"""
AegisPath FastAPI Application Entrypoint.
Provides high-throughput REST APIs for enterprise graph management,
GNN attack path prediction, attention-based XAI, and counterfactual defense simulations.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes import (
    graphs_router,
    prediction_router,
    explain_router,
    defense_router,
    experiments_router,
)

app = FastAPI(
    title="AegisPath API",
    description="AI-Powered Enterprise Attack Path Prediction & Security Decision Support System",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for React frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all local frontend ports (Vite 5173, Next.js 3000)
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


@app.get("/", tags=["Health"])
def root():
    """API welcome and health status."""
    return {
        "system": "AegisPath",
        "status": "online",
        "description": "AI-Powered Enterprise Attack Path Prediction and Decision Support System",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Service liveness probe."""
    return {"status": "healthy", "service": "aegispath-backend"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
