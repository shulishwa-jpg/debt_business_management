from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from app.database import get_db

from app.security import get_current_active_user


from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload


from app.models import (
    User,
    Customer,
    Debt,
    Payment,

    Supplier,
    SupplierDebt,
    SupplierPayment,
)

from app.database import get_db

from app.security import get_current_active_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])



@router.get("/")
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    business_name = current_user.business_name

    # =========================
    # TOTAL CUSTOMERS (light query)
    # =========================
    total_customers = db.query(func.count(Customer.id)).filter(
        Customer.user_id == current_user.id,
        Customer.is_active == True
    ).scalar()

    # =========================
    # TOTAL DEBT (safe)
    # =========================
    payments_subq = db.query(
        Payment.debt_id,
        func.coalesce(func.sum(Payment.amount), 0).label("paid")
    ).group_by(Payment.debt_id).subquery()

    total_debt = db.query(
        func.coalesce(
            func.sum(Debt.amount - func.coalesce(payments_subq.c.paid, 0)),
            0
        )
    ).outerjoin(
        payments_subq, payments_subq.c.debt_id == Debt.id
    ).filter(
        Debt.user_id == current_user.id,
        Debt.is_active == True
    ).scalar()

    # =========================
    # OVERDUE DEBT
    # =========================
    today = datetime.utcnow()

    total_overdue_debt = db.query(
        func.coalesce(
            func.sum(Debt.amount - func.coalesce(payments_subq.c.paid, 0)),
            0
        )
    ).outerjoin(
        payments_subq, payments_subq.c.debt_id == Debt.id
    ).filter(
        Debt.user_id == current_user.id,
        Debt.is_active == True,
        Debt.due_date < today
    ).scalar()

    # =========================
    # STEP 1: GET CUSTOMERS (NO HEAVY JOINS)
    # =========================
    customers = db.query(Customer).filter(
        Customer.user_id == current_user.id,
        Customer.is_active == True
    ).all()

    # =========================
    # STEP 2: GET DEBTS + PAYMENTS (ONLY ONCE)
    # =========================
    debts = db.query(Debt).filter(
        Debt.user_id == current_user.id,
        Debt.is_active == True
    ).all()

    payments = db.query(Payment).all()

    # =========================
    # STEP 3: BUILD DEBT MAP
    # =========================
    payment_map = {}
    for p in payments:
        payment_map[p.debt_id] = payment_map.get(p.debt_id, 0) + p.amount

    customer_debt = {}

    for d in debts:
        paid = payment_map.get(d.id, 0)
        remaining = d.amount - paid

        customer_debt[d.customer_id] = customer_debt.get(d.customer_id, 0) + remaining

    # =========================
    # STEP 4: SORT CUSTOMERS BY DEBT
    # =========================
    customers_sorted = sorted(
        customers,
        key=lambda c: customer_debt.get(c.id, 0),
        reverse=True
    )[:10]

    # =========================
    # RESPONSE
    # =========================
    return {
        "business_name": business_name,
        "total_customers": total_customers,
        "total_debt": total_debt or 0,
        "total_overdue_debt": total_overdue_debt or 0,
        "customers": [
            {
                "uuid": str(c.uuid),
                "name": c.name,
                "phone": c.phone
            }
            for c in customers_sorted
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

    # =====================================================
    # CUSTOMERS
    # =====================================================
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

            "created_at": c.created_at,
        })

    # =====================================================
    # CUSTOMER DEBTS
    # =====================================================
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

        # skip invalid relations
        if not d.customer or not d.customer.uuid:
            continue

        total_paid = sum(
            p.amount for p in d.payments
        )

        remaining = max(
            d.amount - total_paid,
            0
        )

        debt_list.append({

            "uuid": str(d.uuid),

            "customer_uuid":
                str(d.customer.uuid),

            "description":
                d.description,

            "amount":
                d.amount,

            "remaining":
                remaining,

            "taken_date":
                d.taken_date,

            "due_date":
                d.due_date,

            "created_at":
                d.created_at,
        })

    # =====================================================
    # CUSTOMER PAYMENTS
    # =====================================================
    payments = db.query(Payment).options(
        joinedload(Payment.debt)
    ).filter(
        Payment.user_id == current_user.id,
        Payment.uuid != None
    ).all()

    payment_list = []

    for p in payments:

        # skip invalid relations
        if not p.debt or not p.debt.uuid:
            continue

        payment_list.append({

            "uuid": str(p.uuid),

            "debt_uuid":
                str(p.debt.uuid),

            "amount":
                p.amount,

            "receipt_number":
                p.receipt_number,

            "payment_date":
                p.payment_date,

            "created_at":
                p.created_at,
        })

    # =====================================================
    # SUPPLIERS
    # =====================================================
    suppliers = db.query(Supplier).filter(
        Supplier.user_id == current_user.id,
        Supplier.is_active == True,
        Supplier.uuid != None
    ).all()

    supplier_list = []

    for s in suppliers:

        supplier_list.append({

            "uuid": str(s.uuid),

            "business_name":
                s.business_name,

            "paybill":
                s.paybill,

            "account_number":
                s.account_number,

            "phone":
                s.phone,

            "address":
                s.address,

            "created_at":
                s.created_at,
        })

    # =====================================================
    # SUPPLIER DEBTS
    # =====================================================
    supplier_debts = db.query(
        SupplierDebt
    ).options(
        joinedload(SupplierDebt.payments),
        joinedload(SupplierDebt.supplier)
    ).filter(
        SupplierDebt.user_id == current_user.id,
        SupplierDebt.is_active == True,
        SupplierDebt.uuid != None
    ).all()

    supplier_debt_list = []

    for d in supplier_debts:

        # skip invalid relations
        if not d.supplier or not d.supplier.uuid:
            continue

        total_paid = sum(
            p.amount for p in d.payments
        )

        remaining = max(
            d.amount - total_paid,
            0
        )

        supplier_debt_list.append({

            "uuid": str(d.uuid),

            "supplier_uuid":
                str(d.supplier.uuid),

            "item_name":
                d.item_name,

            "amount":
                d.amount,

            "remaining":
                remaining,

            "paid":
                total_paid,

            "supplied_date":
                d.supplied_date,

            "due_date":
                d.due_date,

            "created_at":
                d.created_at,
        })

    # =====================================================
    # SUPPLIER PAYMENTS
    # =====================================================
    supplier_payments = db.query(
        SupplierPayment
    ).options(
        joinedload(SupplierPayment.supplier_debt)
    ).filter(
        SupplierPayment.user_id == current_user.id,
        SupplierPayment.uuid != None
    ).all()

    supplier_payment_list = []

    for p in supplier_payments:

        # skip invalid relations
        if not p.supplier_debt or not p.supplier_debt.uuid:
            continue

        supplier_payment_list.append({

            "uuid": str(p.uuid),

            "debt_uuid":
                str(p.supplier_debt.uuid),

            "amount":
                p.amount,

            "transaction_code":
                p.transaction_code,

            "payment_date":
                p.payment_date,

            "created_at":
                p.created_at,
        })

    # =====================================================
    # RETURN
    # =====================================================
    return {

        # ==========================================
        # CUSTOMER SIDE
        # ==========================================
        "customers": customer_list,

        "debts": debt_list,

        "payments": payment_list,

        # ==========================================
        # SUPPLIER SIDE
        # ==========================================
        "suppliers": supplier_list,

        "supplier_debts":
            supplier_debt_list,

        "supplier_payments":
            supplier_payment_list,
    }



