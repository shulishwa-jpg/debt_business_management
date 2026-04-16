from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from sqlalchemy import func

from app.database import get_db
from app.models import Debt, Customer, User, Payment
from app.security import get_current_active_user
from app.schemas import DebtCreate, PaymentCreate
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload



router = APIRouter(tags=["Debts"])


# ======================================================
# GET ALL DEBTS FOR A CUSTOMER
# GET /customers/{customer_id}/debts
# ======================================================



@router.get("/customers/{customer_uuid}/debts")
def get_customer_debts(
    customer_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    customer = db.query(Customer).filter(
        Customer.uuid == customer_uuid,
        Customer.user_id == current_user.id,
        Customer.is_active == True
    ).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    debts = db.query(Debt).options(
        joinedload(Debt.payments)
    ).filter(
        Debt.customer_id == customer.id,  # 🔥 internal ID
        Debt.user_id == current_user.id,
        Debt.is_active == True
    ).all()

    results = []

    for debt in debts:
        total_paid = sum(p.amount for p in debt.payments)
        remaining = debt.amount - total_paid

        results.append({
            "uuid": str(debt.uuid),
            "description": debt.description,
            "amount": debt.amount,
            "paid": total_paid,
            "remaining": remaining,
            "taken_date": debt.taken_date,
            "due_date": debt.due_date,
            "payments": [
                {
                    "uuid": str(p.uuid),
                    "amount": p.amount,
                    "receipt_number": p.receipt_number,
                    "payment_date": p.created_at
                }
                for p in debt.payments
            ]
        })

    return results

# ======================================================
# ADD DEBT TO CUSTOMER
# POST /customers/{customer_id}/debts
# ======================================================

@router.post("/customers/{customer_uuid}/debts")
def add_debt(
    customer_uuid: str,
    data: DebtCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    customer = db.query(Customer).filter(
        Customer.uuid == customer_uuid,
        Customer.user_id == current_user.id,
        Customer.is_active == True
    ).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    debt = Debt(
        uuid=data.uuid,
        user_id=current_user.id,
        customer_id=customer.id,  # 🔥 internal ID
        description=data.item,
        amount=data.amount,
        taken_date=data.taken_date,
        due_date=data.due_date,
        created_at=datetime.utcnow(),
        is_active=True
    )

    db.add(debt)
    db.commit()
    db.refresh(debt)

    return {
        "uuid": str(debt.uuid),
        "message": "Debt created"
    }


# ======================================================
# ADD PAYMENT TO DEBT
# ======================================================
# ADD PAYMENT
# POST /debts/{debt_id}/payments
# ======================================================

@router.post("/debts/{debt_uuid}/payments")
def add_payment(
    debt_uuid: str,
    data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    debt = db.query(Debt).options(joinedload(Debt.payments)).filter(
        Debt.uuid == debt_uuid,
        Debt.user_id == current_user.id,
        Debt.is_active == True
    ).first()

    if not debt:
        raise HTTPException(status_code=404, detail="Debt not found")

    total_paid = sum(p.amount for p in debt.payments)
    remaining = debt.amount - total_paid

    if data.amount <= 0 or data.amount > remaining:
        raise HTTPException(
            status_code=400,
            detail=f"Amount must be > 0 and <= {remaining}"
        )

    existing = db.query(Payment).filter(
        Payment.receipt_number == data.receipt_number,
        Payment.user_id == current_user.id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Receipt exists")

    payment = Payment(
        uuid=data.uuid,
        debt_id=debt.id,
        user_id=current_user.id,
        amount=data.amount,
        receipt_number=data.receipt_number,
        payment_date=data.payment_date or datetime.utcnow(),
        created_at=datetime.utcnow()
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    return {
        "uuid": str(payment.uuid),
        "remaining_debt": remaining - data.amount
    }

# ======================================================
# UPDATE DEBT
# PUT /debts/{debt_id}
# ======================================================



@router.put("/debts/{debt_uuid}")
def update_debt(
    debt_uuid: str,
    data: DebtCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    debt = db.query(Debt).filter(
        Debt.uuid == debt_uuid,
        Debt.user_id == current_user.id,
        Debt.is_active == True
    ).first()

    if not debt:
        raise HTTPException(status_code=404, detail="Debt not found")

    debt.description = data.item
    debt.amount = data.amount
    debt.taken_date = data.taken_date
    debt.due_date = data.due_date

    db.commit()
    return {"message": "Debt updated"}

# ======================================================
# DELETE DEBT (SOFT DELETE)
# DELETE /debts/{debt_id}
# ======================================================

@router.delete("/debts/{debt_uuid}")
def delete_debt(
    debt_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    debt = db.query(Debt).filter(
        Debt.uuid == debt_uuid,
        Debt.user_id == current_user.id,
        Debt.is_active == True
    ).first()

    if not debt:
        raise HTTPException(status_code=404, detail="Debt not found")

    total_paid = db.query(
        func.coalesce(func.sum(Payment.amount), 0)
    ).filter(
        Payment.debt_id == debt.id,
        Payment.user_id == current_user.id
    ).scalar()

    remaining = debt.amount - total_paid

    if remaining != 0:
        raise HTTPException(
            status_code=400,
            detail="Debt must be fully paid before deletion"
        )

    # 🔥 delete payments first
    db.query(Payment).filter(
        Payment.debt_id == debt.id,
        Payment.user_id == current_user.id
    ).delete()

    # 🔥 delete debt permanently
    db.delete(debt)

    db.commit()

    return {"message": "Debt and payments deleted permanently"}


# ======================================================
# GET CUSTOMER DETAILS + TOTALS
# ======================================================

@router.get("/customers/{customer_uuid}")
def get_customer_details(
    customer_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    customer = db.query(Customer).filter(
        Customer.uuid == customer_uuid,
        Customer.user_id == current_user.id,
        Customer.is_active == True
    ).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    debts = db.query(Debt).filter(
        Debt.customer_id == customer.id,
        Debt.user_id == current_user.id,
        Debt.is_active == True
    ).all()

    total_remaining = 0
    overdue = 0

    for debt in debts:
        total_paid = db.query(func.coalesce(func.sum(Payment.amount), 0))\
            .filter(Payment.debt_id == debt.id).scalar()

        remaining = debt.amount - total_paid
        total_remaining += remaining

        if debt.due_date < datetime.utcnow() and remaining > 0:
            overdue += remaining

    return {
        "uuid": str(customer.uuid),
        "name": customer.name,
        "phone": customer.phone,
        "total_debt": float(total_remaining),
        "overdue_debt": float(overdue)
    }