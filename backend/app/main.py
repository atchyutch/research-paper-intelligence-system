# import uvicorn
# from fastapi import FastAPI
# from starlette.middleware.cors import CORSMiddleware
#
# from backend.app.api.v1.router import api_router
#
# app = FastAPI(title="Research Paper Intelligence System")
#
# @app.on_event("startup")
# def startup():
#     from backend.app.db.base import Base
#     from backend.app.db.session import engine
#     Base.metadata.create_all(bind=engine)
#
# app.include_router(api_router, prefix="/api")
#
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
# )


from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from backend.app.api.v1.router import api_router

app = FastAPI(title="Research Paper Intelligence System")

app.include_router(api_router, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
)