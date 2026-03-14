from fastapi import APIRouter, FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.api.deps import get_db

router = APIRouter(prefix = "/db_health", tags = ["db_health"])

@router.get("")
def db_ping(db: Session = Depends(get_db)) -> dict [str,bool]:
    db.execute(text("SELECT 1"))
    return {"db": True}
