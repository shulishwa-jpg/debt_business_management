from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database import get_db
from app.models import Subscription, User, Payment
from app.security import get_current_user
from app.stk_push import send_stk_push

router = APIRouter(prefix="/mpesa", tags=["M-Pesa"])

from pydantic import BaseModel

class STKPushRequest(BaseModel):
    phone: str


@router.post("/stk-push")
def stk_push_route(
    data: STKPushRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    callback_url = "https://testily-complemented-berry.ngrok-free.dev/mpesa/callback"

    return send_stk_push(
        phone=data.phone,
        amount=1,
        callback_url=callback_url
    )

@router.post("/callback")
async def mpesa_callback(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
    except Exception:
        return {"ResultCode": 0, "ResultDesc": "Invalid JSON"}

    try:
        stk = data.get("Body", {}).get("stkCallback", {})
        result_code = stk.get("ResultCode")
        if result_code != 0:
            return {"ResultCode": 0, "ResultDesc": "Payment not successful"}

        metadata = stk.get("CallbackMetadata", {}).get("Item", [])
        phone = None
        amount = None
        receipt = None
        for item in metadata:
            if item.get("Name") == "PhoneNumber":
                phone = str(item.get("Value"))
            elif item.get("Name") == "Amount":
                amount = float(item.get("Value"))
            elif item.get("Name") == "MpesaReceiptNumber":
                receipt = item.get("Value")

        if not phone or not receipt or amount is None:
            return {"ResultCode": 0, "ResultDesc": "Missing payment data"}

        if phone.startswith("254"):
            phone = "0" + phone[3:]

        user = db.query(User).filter(User.phone == phone).first()
        if not user:
            return {"ResultCode": 0, "ResultDesc": "User not found"}

        existing_payment = db.query(Payment).filter(
            Payment.receipt_number == receipt
        ).first()
        if existing_payment:
            return {"ResultCode": 0, "ResultDesc": "Already processed"}

        PLAN_PRICE = 1
        if round(float(amount), 2) != round(float(PLAN_PRICE), 2):
            return {"ResultCode": 0, "ResultDesc": "Invalid amount"}

        payment = Payment(
            user_id=user.id,
            amount=amount,
            receipt_number=receipt,
            created_at=datetime.utcnow()
        )
        db.add(payment)

        existing_sub = db.query(Subscription).filter(
            Subscription.user_id == user.id,
            Subscription.status == "active"
        ).first()
        if existing_sub:
            existing_sub.end_date += timedelta(days=30)
        else:
            new_sub = Subscription(
                user_id=user.id,
                plan_name="monthly",
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=30),
                status="active"
            )
            db.add(new_sub)

        db.commit()
        return {"ResultCode": 0, "ResultDesc": "Processed successfully"}
    except Exception as e:
        db.rollback()
        return {"ResultCode": 0, "ResultDesc": "Processing error"}

@router.get("/subscription/status")
def subscription_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sub = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == "active"
    ).first()

    if not sub:
        return {
            "active": False,
            "reason": "no_subscription"
        }

    if sub.end_date < datetime.utcnow():
        sub.status = "expired"
        db.commit()

        return {
            "active": False,
            "reason": "expired"
        }

    return {
        "active": True,
        "end_date": sub.end_date
    }