from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Depends
from sqlalchemy.exc import NoResultFound, IntegrityError

from backend.app.api.deps import get_db
from backend.app.api.v1.models import UserRequest
from backend.app.core.config import settings
from backend.app.db.base import Users
import bcrypt
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer

import hashlib

auth_router = APIRouter()

# Retrieves the token from the url header and gives to us
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


@auth_router.post("/create_user")
async def create_user(first_name:str, last_name:str, email:str, password:str,
                      response_model:UserRequest, db = Depends(get_db), status_code=status.HTTP_201_CREATED):
    hashed_password = password_hasher(password)
    new_user = Users(
        first_name=first_name,
        last_name=last_name,
        email=email,
        hashed_password=hashed_password
    )
    try:
        db.add(new_user)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    finally:
        db.commit()
    return {"Status": "Success"}


@auth_router.post("/login")
async def login(email:str, password:str, db = Depends(get_db)):
    try:
        retrieved_user = db.query(Users).filter(Users.email == email).first()
        retrieved_password = retrieved_user.hashed_password

        if bcrypt.checkpw(password.encode("utf-8"), retrieved_password.encode("utf-8")):
            # Create a jwt token which is valid for 2 hours.
            payload = {"user_id": retrieved_user.user_id, "user_email": retrieved_user.email, "exp": datetime.now(
                timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)}
            token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM, headers={"alg": "HS256", "typ": "JWT"})
            return {"token": token}
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect Password")
    except NoResultFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Email is not found in the database:  {e}")


def password_hasher(password):
    # Hash the password with salt
    salt = bcrypt.gensalt()

    # Hash password along with salt, encode the password as the salt is already encoded and then
    # decode the entire thing into string
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
    return hashed_password


def get_current_user(token: str = Depends(oauth2_scheme), db = Depends(get_db)):
    try:
        decoded = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        retrieved_user_id = decoded.get("user_id", None)
        if retrieved_user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tampered JWT")
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    user = db.query(Users).filter(Users.user_id == retrieved_user_id).first()
    if not user:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

