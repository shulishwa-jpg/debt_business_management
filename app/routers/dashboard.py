from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from app.database import get_db
from app.models import User, Customer, Debt, Payment
from app.security import get_current_active_user


from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Customer, Debt, Payment, User
from app.security import get_current_active_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/")
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    business_name = current_user.business_name

    # ✅ TOTAL CUSTOMERS (no .all())
    total_customers = db.query(func.count(Customer.id)).filter(
        Customer.user_id == current_user.id,
        Customer.is_active == True
    ).scalar()

    # ✅ TOTAL DEBT (remaining)
    total_debt = db.query(
        func.coalesce(func.sum(Debt.amount), 0)
        - func.coalesce(func.sum(Payment.amount), 0)
    ).outerjoin(
        Payment, Payment.debt_id == Debt.id
    ).filter(
        Debt.user_id == current_user.id,
        Debt.is_active == True
    ).scalar()

    # ✅ OVERDUE DEBT
    today = datetime.utcnow()

    total_overdue_debt = db.query(
        func.coalesce(func.sum(Debt.amount), 0)
        - func.coalesce(func.sum(Payment.amount), 0)
    ).outerjoin(
        Payment, Payment.debt_id == Debt.id
    ).filter(
        Debt.user_id == current_user.id,
        Debt.is_active == True,
        Debt.due_date < today
    ).scalar()

    # ✅ RECENT CUSTOMERS (limit for UI)
    customers = db.query(Customer).filter(
        Customer.user_id == current_user.id,
        Customer.is_active == True
    ).order_by(Customer.created_at.desc()).limit(10).all()

    return {
        "business_name": business_name,
        "total_customers": total_customers,
        "total_debt": total_debt or 0,
        "total_overdue_debt": total_overdue_debt or 0,
        "customers": [
            {
                "uuid": str(customer.uuid),  # ✅ UUID here
                "name": customer.name,
                "phone": customer.phone
            }
            for customer in customers
        ]
    }


from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Customer, Debt, Payment, User
from app.security import get_current_active_user




@router.get("/full-data")
def get_full_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):

    # =========================
    # CUSTOMERS
    # =========================
    customers = db.query(Customer).filter(
        Customer.user_id == current_user.id,
        Customer.is_active == True,
        Customer.uuid != None
    ).all()

    customer_list = []
    for c in customers:
        customer_list.append({
            "uuid": str(c.uuid),
            "name": c.name,
            "phone": c.phone,
            "address": c.address,
            "created_at": c.created_at
        })

    # =========================
    # DEBTS (WITH PAYMENTS)
    # =========================
    debts = db.query(Debt).options(
        joinedload(Debt.payments),
        joinedload(Debt.customer)
    ).filter(
        Debt.user_id == current_user.id,
        Debt.is_active == True,
        Debt.uuid != None
    ).all()

    debt_list = []
    for d in debts:
        # skip if customer missing or uuid missing
        if not d.customer or not d.customer.uuid:
            continue

        total_paid = sum(p.amount for p in d.payments)
        remaining = max(d.amount - total_paid, 0)

        debt_list.append({
            "uuid": str(d.uuid),
            "customer_uuid": str(d.customer.uuid),
            "description": d.description,
            "amount": d.amount,
            "remaining": remaining,
            "taken_date": d.taken_date,
            "due_date": d.due_date,
            "created_at": d.created_at
        })

    # =========================
    # PAYMENTS
    # =========================
    payments = db.query(Payment).options(
        joinedload(Payment.debt)
    ).filter(
        Payment.user_id == current_user.id,
        Payment.uuid != None
    ).all()

    payment_list = []
    for p in payments:
        # skip if debt missing or uuid missing
        if not p.debt or not p.debt.uuid:
            continue

        payment_list.append({
            "uuid": str(p.uuid),
            "debt_uuid": str(p.debt.uuid),
            "amount": p.amount,
            "receipt_number": p.receipt_number,
            "payment_date": p.payment_date,
            "created_at": p.created_at
        })

    return {
        "customers": customer_list,
        "debts": debt_list,
        "payments": payment_list
    }