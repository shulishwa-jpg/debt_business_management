from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import User, Subscription
from .auth import SECRET_KEY, ALGORITHM


# ✅ Proper token extractor
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ==========================
# DB SESSION
# ==========================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==========================
# GET CURRENT USER (FIXED)
# ==========================
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # ✅ FIX: use correct key
        user_id = payload.get("user_id")

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return user

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ==========================
# REQUIRE SUBSCRIPTION (FIXED)
# ==========================
def require_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sub = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == "active"
    ).first()

    if not sub:
        raise HTTPException(
            status_code=403,
            detail="Subscription inactive or expired"
        )

    return current_user