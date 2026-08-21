"""Backend API Routers."""

from backend.routes.graphs import router as graphs_router
from backend.routes.prediction import router as prediction_router
from backend.routes.explain import router as explain_router
from backend.routes.defense import router as defense_router
from backend.routes.experiments import router as experiments_router

__all__ = [
    "graphs_router",
    "prediction_router",
    "explain_router",
    "defense_router",
    "experiments_router",
]
