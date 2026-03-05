from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models import User, Customer, Debt
from app.security import get_current_active_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


from sqlalchemy import func
from app.models import Payment
from datetime import datetime


@router.get("/")
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    business_name = current_user.business_name

    customers = db.query(Customer).filter(
        Customer.user_id == current_user.id,
        Customer.is_active == True
    ).all()

    total_customers = len(customers)

    debts = db.query(Debt).filter(
        Debt.user_id == current_user.id,
        Debt.is_active == True
    ).all()

    total_debt = 0
    total_overdue_debt = 0
    today = datetime.utcnow()

    for debt in debts:
        total_paid = db.query(
            func.coalesce(func.sum(Payment.amount), 0)
        ).filter(
            Payment.debt_id == debt.id
        ).scalar()

        remaining = debt.amount - total_paid

        total_debt += remaining

        if debt.due_date and debt.due_date < today:
            total_overdue_debt += remaining

    return {
        "business_name": business_name,
        "total_customers": total_customers,
        "total_debt": total_debt,
        "total_overdue_debt": total_overdue_debt,
        "customers": [
            {
                "id": customer.id,
                "name": customer.name,
                "phone": customer.phone
            }
            for customer in customers
        ]
    }