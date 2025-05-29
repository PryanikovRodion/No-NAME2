import bcrypt
from datetime import datetime, timedelta, timezone
import jwt
from sqlmodel import Session
from fastapi import Depends, HTTPException, Header
from database.db import *


secret_key = "your_secret_key"
algorithm = "HS256"


def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def generate_token(user_id: int) -> str:
    expiration = datetime.now(timezone.utc) + timedelta(days=1)
    exp_timestamp = int(expiration.timestamp())
    token = jwt.encode({"sub": str(user_id), "exp": exp_timestamp}, secret_key, algorithm=algorithm)
    return token

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
def get_curent_user(db: Session = Depends(get_session), token: str = Header()):
    if not token:
        raise HTTPException(status_code=401, detail="Token not provided")
    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub"))
        from database.models import User
        user = db.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

def get_buyer(user = Depends(get_curent_user)):
    from database.models import Role
    if user.role != Role.buyer:
        raise HTTPException(status_code=403, detail="Not authorized as a buyer")
    return user

def get_seller(user = Depends(get_curent_user)):
    from database.models import Role
    if user.role != Role.seller:
        raise HTTPException(status_code=403, detail="Not authorized as a seller")
    return user