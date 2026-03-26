from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import RegisterRequest, LoginRequest, ResetPasswordRequest
from passlib.context import CryptContext
from app.security import create_access_token, create_refresh_token, verify_refresh_token

router = APIRouter(prefix="/auth", tags=["Auth"])

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


# 🔐 Password Helpers
def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)


# 📝 Register
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


# 🔑 Login (UPDATED 🔥)
@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == data.phone).first()

    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # ✅ Create both tokens
    access_token = create_access_token({"user_id": user.id})
    refresh_token = create_refresh_token({"user_id": user.id})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


# 🔄 Refresh Token Endpoint (NEW 🔥)
from pydantic import BaseModel

class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/refresh")
def refresh_token(data: RefreshRequest):
    payload = verify_refresh_token(data.refresh_token)

    new_access_token = create_access_token({
        "user_id": payload["user_id"]
    })

    return {"access_token": new_access_token}


# 🔁 Reset Password
@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):

    if data.new_password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    user = db.query(User).filter(
        User.phone == data.phone,
        User.business_name == data.business_name
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password = hash_password(data.new_password)
    db.commit()

    return {"message": "Password reset successful"}