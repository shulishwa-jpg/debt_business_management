from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database import get_db
from app.models import Subscription, User
from app.schemas import SubscriptionCreate, SubscriptionResponse
from app.security import get_current_active_user

router = APIRouter(prefix="/subscription", tags=["Subscription"])





# CREATE PAID SUBSCRIPTION
@router.post("/create", response_model=SubscriptionResponse)
def create_subscription(
    data: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    existing = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == "active"
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Already has active subscription")

    end_date = datetime.utcnow() + timedelta(days=data.duration_days)

    subscription = Subscription(
        user_id=current_user.id,
        plan_name=data.plan_name,
        start_date=datetime.utcnow(),
        end_date=end_date,
        status="active"
    )

    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    return subscription


@router.get("/status")
def check_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).order_by(Subscription.id.desc()).first()

    if not subscription:
        return {
            "active": False,
            "end_date": None
        }

    now = datetime.utcnow()

    # 🔥 CHECK EXPIRY
    is_active = (
        subscription.status == "active"
        and subscription.end_date is not None
        and subscription.end_date > now
    )

    # update status if expired
    if subscription.end_date and subscription.end_date <= now:
        subscription.status = "expired"
        db.commit()

    return {
        "active": is_active,
        "end_date": subscription.end_date,
        "plan_name": subscription.plan_name,
        "uuid": str(subscription.uuid)
    }
