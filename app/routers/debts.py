from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from sqlalchemy import func

from app.database import get_db
from app.models import Debt, Customer, User, Payment
from app.security import get_current_active_user
from app.schemas import DebtCreate, PaymentCreate

router = APIRouter(tags=["Debts"])


# ======================================================
# GET ALL DEBTS FOR A CUSTOMER
# GET /customers/{customer_id}/debts
# ======================================================

@router.get("/customers/{customer_id}/debts")
def get_customer_debts(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.user_id == current_user.id,
        Customer.is_active == True
    ).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    debts = db.query(Debt).filter(
        Debt.customer_id == customer_id,
        Debt.user_id == current_user.id,
        Debt.is_active == True
    ).all()

    results = []

    for debt in debts:
        total_paid = db.query(
            func.coalesce(func.sum(Payment.amount), 0)
        ).filter(
            Payment.debt_id == debt.id
        ).scalar()

        remaining = debt.amount - total_paid

        payments = db.query(Payment).filter(
            Payment.debt_id == debt.id
        ).all()

        payment_list = [
            {
                "id": p.id,
                "amount": p.amount,
                "receipt_number": p.receipt_number,
                "payment_date": p.created_at
            }
            for p in payments
        ]

        results.append({
            "id": debt.id,
            "description": debt.description,
            "amount": debt.amount,
            "paid": total_paid,
            "remaining": remaining,
            "taken_date": debt.taken_date,
            "due_date": debt.due_date,
            "payments": payment_list
        })

    return results


# ======================================================
# ADD DEBT TO CUSTOMER
# POST /customers/{customer_id}/debts
# ======================================================

@router.post("/customers/{customer_id}/debts")
def add_debt(
    customer_id: int,
    data: DebtCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.user_id == current_user.id,
        Customer.is_active == True
    ).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    debt = Debt(
        user_id=current_user.id,
        customer_id=customer_id,
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

    return debt


# ======================================================
# ADD PAYMENT TO DEBT
# ======================================================
# ADD PAYMENT
# POST /debts/{debt_id}/payments
# ======================================================

@router.post("/{debt_id}/payments")
def add_payment(
    debt_id: int,
    data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # ==========================
    # CHECK DEBT EXISTS
    # ==========================
    debt = db.query(Debt).filter(
        Debt.id == debt_id,
        Debt.user_id == current_user.id,
        Debt.is_active == True
    ).first()

    if not debt:
        raise HTTPException(status_code=404, detail="Debt not found")

    # ==========================
    # VALIDATE AMOUNT
    # ==========================
    total_paid = sum(p.amount for p in debt.payments)
    remaining = debt.amount - total_paid

    if data.amount <= 0 or data.amount > remaining:
        raise HTTPException(
            status_code=400,
            detail=f"Amount must be > 0 and <= {remaining}"
        )

    # ==========================
    # CHECK DUPLICATE RECEIPT
    # ==========================
    existing_payment = db.query(Payment).filter(
        Payment.receipt_number == data.receipt_number,
        Payment.user_id == current_user.id
    ).first()

    if existing_payment:
        raise HTTPException(
            status_code=400,
            detail="Receipt number already exists"
        )

    # ==========================
    # CREATE PAYMENT
    # ==========================
    payment = Payment(
        debt_id=debt.id,
        user_id=current_user.id,
        amount=data.amount,
        receipt_number=data.receipt_number,
        payment_date=data.payment_date or datetime.utcnow(),
        created_at=datetime.utcnow()
    )

    try:
        db.add(payment)
        db.commit()
        db.refresh(payment)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Receipt number already exists"
        )

    # ==========================
    # RETURN RESPONSE
    # ==========================
    return {
        "message": "Payment added successfully",
        "payment": {
            "id": payment.id,
            "debt_id": payment.debt_id,
            "amount": payment.amount,
            "receipt_number": payment.receipt_number,
            "payment_date": payment.payment_date,
            "created_at": payment.created_at
        },
        "remaining_debt": remaining - data.amount
    }

# ======================================================
# UPDATE DEBT
# PUT /debts/{debt_id}
# ======================================================

@router.put("/debts/{debt_id}")
def update_debt(
    debt_id: int,
    data: DebtCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    debt = db.query(Debt).filter(
        Debt.id == debt_id,
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
    db.refresh(debt)

    return {"message": "Debt updated successfully"}


# ======================================================
# DELETE DEBT (SOFT DELETE)
# DELETE /debts/{debt_id}
# ======================================================

@router.delete("/debts/{debt_id}")
def delete_debt(
    debt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    debt = db.query(Debt).filter(
        Debt.id == debt_id,
        Debt.user_id == current_user.id
    ).first()

    if not debt:
        raise HTTPException(status_code=404, detail="Debt not found")

    total_paid = db.query(
        func.coalesce(func.sum(Payment.amount), 0)
    ).filter(
        Payment.debt_id == debt.id
    ).scalar()

    remaining = debt.amount - total_paid

    if remaining > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete unpaid debt"
        )

    debt.is_active = False
    db.commit()

    return {"message": "Debt deleted successfully"}


# ======================================================
# GET CUSTOMER DETAILS + TOTALS
# ======================================================

@router.get("/customers/{customer_id}")
def get_customer_details(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.user_id == current_user.id,
        Customer.is_active == True
    ).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    debts = db.query(Debt).filter(
        Debt.customer_id == customer_id,
        Debt.user_id == current_user.id,
        Debt.is_active == True
    ).all()

    total_remaining = 0
    overdue_remaining = 0

    for debt in debts:
        total_paid = db.query(
            func.coalesce(func.sum(Payment.amount), 0)
        ).filter(
            Payment.debt_id == debt.id
        ).scalar()

        remaining = debt.amount - total_paid
        total_remaining += remaining

        if debt.due_date < datetime.utcnow() and remaining > 0:
            overdue_remaining += remaining

    return {
        "id": customer.id,
        "name": customer.name,
        "phone": customer.phone,
        "total_debt": float(total_remaining),
        "overdue_debt": float(overdue_remaining)
    }