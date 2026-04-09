from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import Customer, User, Debt
from app.schemas import CustomerCreate, CustomerUpdate, CustomerResponse
from app.security import get_current_active_user

router = APIRouter(prefix="/customers", tags=["Customers"])


# ✅ CREATE CUSTOMER
@router.post("/", response_model=CustomerResponse)
def create_customer(
    data: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    customer = Customer(
        uuid=data.uuid,
        user_id=current_user.id,
        name=data.name,
        phone=data.phone,
        address=data.address,
        # uuid auto-generated
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


# ✅ GET ALL CUSTOMERS (ACTIVE ONLY)
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
        .order_by(Customer.created_at.desc())  # optional improvement
        .all()
    )


# ✅ UPDATE CUSTOMER (UUID)
@router.put("/{customer_uuid}", response_model=CustomerResponse)
def update_customer(
    customer_uuid: str,
    data: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    customer = (
        db.query(Customer)
        .filter(
            Customer.uuid == customer_uuid,
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


# ✅ DELETE CUSTOMER (UUID)
@router.delete("/{customer_uuid}")
def delete_customer(
    customer_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    customer = db.query(Customer).filter(
        Customer.uuid == customer_uuid,
        Customer.user_id == current_user.id
    ).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # 🔥 IMPORTANT: use internal ID here
    total_debt = db.query(
        func.coalesce(func.sum(Debt.amount), 0)
    ).filter(
        Debt.customer_id == customer.id,
        Debt.user_id == current_user.id,
        Debt.is_active == True
    ).scalar()

    if total_debt > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete customer. They still owe KSh {total_debt:.0f}"
        )

    # ✅ soft delete
    customer.is_active = False
    db.commit()

    return {"message": "Customer deleted"}