from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer

from backend.app.db.session import sessionLocal

def get_db():
    db = None
    try:
        db = sessionLocal()
        yield db
    finally:
        if db is not None:
            db.close()

