from fastapi import Depends, HTTPException
from jose import jwt
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import User, Subscription
from .auth import SECRET_KEY, ALGORITHM


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(token: str = Depends(lambda: None), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user = db.query(User).get(int(payload["sub"]))
        if not user:
            raise Exception()
        return user
    except:
        raise HTTPException(status_code=401, detail="Invalid token")


def require_subscription(user=Depends(get_current_user)):
    if not user.subscription or not user.subscription.is_active:
        raise HTTPException(status_code=403, detail="Subscription inactive")
    return user
