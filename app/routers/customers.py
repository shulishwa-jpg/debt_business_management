from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Customer, User
from app.schemas import CustomerCreate, CustomerUpdate, CustomerResponse
from app.security import get_current_user, get_current_active_user


router = APIRouter(prefix="/customers", tags=["Customers"])


# CREATE CUSTOMER
@router.post("/", response_model=CustomerResponse)
def create_customer(
    data: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)

):
    customer = Customer(
        user_id=current_user.id,
        name=data.name,
        phone=data.phone,
        address=data.address,
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


# GET ALL CUSTOMERS (ACTIVE ONLY)
@router.get("/", response_model=list[CustomerResponse])
def get_customers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)

):
    return (
        db.query(Customer)
        .filter(
            Customer.user_id == current_user.id,
            Customer.is_active == True,
        )
        .all()
    )


# UPDATE CUSTOMER
@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: int,
    data: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)

):
    customer = (
        db.query(Customer)
        .filter(
            Customer.id == customer_id,
            Customer.user_id == current_user.id,
            Customer.is_active == True,
        )
        .first()
    )

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    if data.name is not None:
        customer.name = data.name
    if data.phone is not None:
        customer.phone = data.phone
    if data.address is not None:
        customer.address = data.address

    db.commit()
    db.refresh(customer)

    return customer

from app.models import Customer, User, Debt
from sqlalchemy import func


@router.delete("/{customer_id}")
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.user_id == current_user.id
    ).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")


    # ✅ check total active debts
    total_debt = db.query(
        func.coalesce(func.sum(Debt.amount), 0)
    ).filter(
        Debt.customer_id == customer_id,
        Debt.user_id == current_user.id,
        Debt.is_active == True
    ).scalar()


    # ✅ block deletion if any debt exists
    if total_debt > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete customer. They still owe KSh {total_debt:.0f}"
        )


    # soft delete (your existing logic)
    customer.is_active = False
    db.commit()

    return {"message": "Customer deleted"}