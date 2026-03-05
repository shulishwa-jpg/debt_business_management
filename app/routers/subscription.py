from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database import get_db
from app.models import Subscription, User
from app.schemas import SubscriptionCreate, SubscriptionResponse

router = APIRouter(prefix="/subscription", tags=["Subscription"])


# CREATE SUBSCRIPTION
@router.post("/create", response_model=SubscriptionResponse)
def create_subscription(data: SubscriptionCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == data.user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check existing active subscription
    existing = db.query(Subscription).filter(
        Subscription.user_id == data.user_id,
        Subscription.status == "active"
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="User already has active subscription")

    end_date = datetime.utcnow() + timedelta(days=data.duration_days)

    subscription = Subscription(
        user_id=data.user_id,
        plan_name=data.plan_name,
        end_date=end_date,
        status="active"
    )

    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    return subscription


# CHECK SUBSCRIPTION STATUS
@router.get("/status/{user_id}")
def check_subscription(user_id: int, db: Session = Depends(get_db)):
    subscription = db.query(Subscription).filter(
        Subscription.user_id == user_id
    ).order_by(Subscription.id.desc()).first()

    if not subscription:
        return {"status": "no subscription"}

    # Auto expire
    if subscription.end_date < datetime.utcnow():
        subscription.status = "expired"
        db.commit()

    return {
        "plan_name": subscription.plan_name,
        "start_date": subscription.start_date,
        "end_date": subscription.end_date,
        "status": subscription.status
    }
