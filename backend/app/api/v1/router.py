from fastapi import APIRouter
from backend.app.api.v1.endpoints import health, db_health
from backend.app.api.v1.endpoints.document_api import document_router

api_router = APIRouter(prefix="/v1")

# Heath routers will be in the health.py file in the endpoints directory
api_router.include_router(health.router)

# Database Health routes will be in the db_health.py file in the endpoints directory
api_router.include_router(db_health.router)

# Import the document_loading router from the user.
api_router.include_router(document_router)

api_router.include_router()