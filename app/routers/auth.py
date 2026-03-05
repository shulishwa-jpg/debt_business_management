from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import RegisterRequest, LoginRequest
from passlib.context import CryptContext
from app.security import create_access_token

import os

router = APIRouter(prefix="/auth", tags=["Auth"])

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.phone == data.phone).first()
    if existing:
        raise HTTPException(status_code=400, detail="Phone already registered")

    user = User(
        phone=data.phone,
        password=hash_password(data.password),
        business_name=data.business_name,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "Account created successfully"}

@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == data.phone).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    if not verify_password(data.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_access_token({"user_id": user.id})
    return {"access_token": token, "token_type": "bearer"}