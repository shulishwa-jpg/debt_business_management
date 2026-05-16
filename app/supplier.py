from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import datetime

from app.models import Debt

from app.database import get_db
from app.models import (
    Supplier,
    SupplierDebt,
    SupplierPayment,
    User
)
from app.schemas import (
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
    SupplierDebtCreate,
    SupplierPaymentCreate
)
from app.security import get_current_active_user


router = APIRouter(
    prefix="/suppliers",
    tags=["Suppliers"]
)



@router.get("/dashboard")
def get_supplier_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):

    business_name = current_user.business_name

    # ============================================
    # TOTAL SUPPLIERS
    # ============================================
    total_suppliers = db.query(
        func.count(Supplier.id)
    ).filter(
        Supplier.user_id == current_user.id,
        Supplier.is_active == True
    ).scalar() or 0

    # ============================================
    # SUPPLIER DEBTS
    # ============================================
    supplier_debts = db.query(SupplierDebt).options(
        joinedload(SupplierDebt.payments)
    ).filter(
        SupplierDebt.user_id == current_user.id,
        SupplierDebt.is_active == True
    ).all()

    total_supplier_debt = 0
    total_overdue_supplier_debt = 0

    for debt in supplier_debts:

        total_paid = sum(p.amount for p in debt.payments)

        remaining = debt.amount - total_paid

        total_supplier_debt += remaining

        if (
            debt.due_date and
            debt.due_date < datetime.utcnow() and
            remaining > 0
        ):
            total_overdue_supplier_debt += remaining

    # ============================================
    # CUSTOMER DEBT COMPARISON
    # (money owed TO current user)
    # ============================================
    customer_debts = db.query(Debt).options(
        joinedload(Debt.payments)
    ).filter(
        Debt.user_id == current_user.id,
        Debt.is_active == True
    ).all()

    total_customer_debt = 0

    for debt in customer_debts:

        total_paid = sum(p.amount for p in debt.payments)

        remaining = debt.amount - total_paid

        total_customer_debt += remaining

    # ============================================
    # BALANCE
    # ============================================
    balance = total_customer_debt - total_supplier_debt

    # ============================================
    # SUPPLIER LIST
    # ============================================
    suppliers = db.query(Supplier).filter(
        Supplier.user_id == current_user.id,
        Supplier.is_active == True
    ).order_by(
        Supplier.created_at.desc()
    ).all()

    supplier_list = []

    for supplier in suppliers:

        supplier_list.append({
            "uuid": str(supplier.uuid),

            "business_name": supplier.business_name,

            "phone": supplier.phone or "",

            "paybill": supplier.paybill or "",

            "account_number": supplier.account_number or ""
        })

    # ============================================
    # RESPONSE
    # ============================================
    return {

        "business_name": business_name or "",

        "total_supplier_debt": total_supplier_debt or 0,

        "total_overdue_supplier_debt":
            total_overdue_supplier_debt or 0,

        "comparison": {
            "they_owe_me": total_customer_debt or 0,

            "i_owe_suppliers": total_supplier_debt or 0,

            "balance": balance or 0
        },

        "total_suppliers": total_suppliers or 0,

        "suppliers": supplier_list or []
    }



@router.post("/", response_model=SupplierResponse)
def create_supplier(
    data: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):

    supplier = Supplier(
        uuid=data.uuid,
        user_id=current_user.id,

        business_name=data.business_name,

        paybill=data.paybill,
        account_number=data.account_number,

        phone=data.phone,
        address=data.address
    )

    db.add(supplier)
    db.commit()
    db.refresh(supplier)

    return supplier


# =====================================================
# GET ALL SUPPLIERS
# =====================================================
@router.get("/", response_model=list[SupplierResponse])
def get_suppliers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):

    return (
        db.query(Supplier)
        .filter(
            Supplier.user_id == current_user.id,
            Supplier.is_active == True
        )
        .order_by(Supplier.created_at.desc())
        .all()
    )


# =====================================================
# UPDATE SUPPLIER
# =====================================================
@router.put("/{supplier_uuid}", response_model=SupplierResponse)
def update_supplier(
    supplier_uuid: str,
    data: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):

    supplier = (
        db.query(Supplier)
        .filter(
            Supplier.uuid == supplier_uuid,
            Supplier.user_id == current_user.id,
            Supplier.is_active == True
        )
        .first()
    )

    if not supplier:
        raise HTTPException(
            status_code=404,
            detail="Supplier not found"
        )

    if data.business_name is not None:
        supplier.business_name = data.business_name

    if data.paybill is not None:
        supplier.paybill = data.paybill

    if data.account_number is not None:
        supplier.account_number = data.account_number

    if data.phone is not None:
        supplier.phone = data.phone

    if data.address is not None:
        supplier.address = data.address

    db.commit()
    db.refresh(supplier)

    return supplier


# =====================================================
# DELETE SUPPLIER
# =====================================================
@router.delete("/{supplier_uuid}")
def delete_supplier(
    supplier_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):

    supplier = (
        db.query(Supplier)
        .filter(
            Supplier.uuid == supplier_uuid,
            Supplier.user_id == current_user.id
        )
        .first()
    )

    if not supplier:
        raise HTTPException(
            status_code=404,
            detail="Supplier not found"
        )

    total_debt = db.query(
        func.coalesce(func.sum(SupplierDebt.amount), 0)
    ).filter(
        SupplierDebt.supplier_id == supplier.id,
        SupplierDebt.user_id == current_user.id,
        SupplierDebt.is_active == True
    ).scalar()

    total_paid = db.query(
        func.coalesce(func.sum(SupplierPayment.amount), 0)
    ).join(
        SupplierDebt,
        SupplierPayment.supplier_debt_id == SupplierDebt.id
    ).filter(
        SupplierDebt.supplier_id == supplier.id,
        SupplierPayment.user_id == current_user.id
    ).scalar()

    remaining = total_debt - total_paid

    if remaining > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete supplier. You still owe KSh {remaining:.0f}"
        )

    supplier.is_active = False

    db.commit()

    return {"message": "Supplier deleted"}


# =====================================================
# ADD SUPPLIER DEBT
# =====================================================
@router.post("/{supplier_uuid}/debts")
def add_supplier_debt(
    supplier_uuid: str,
    data: SupplierDebtCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):

    supplier = (
        db.query(Supplier)
        .filter(
            Supplier.uuid == supplier_uuid,
            Supplier.user_id == current_user.id,
            Supplier.is_active == True
        )
        .first()
    )

    if not supplier:
        raise HTTPException(
            status_code=404,
            detail="Supplier not found"
        )

    debt = SupplierDebt(
        uuid=data.uuid,

        supplier_id=supplier.id,
        user_id=current_user.id,

        item_name=data.item_name,
        amount=data.amount,

        supplied_date=data.supplied_date,
        due_date=data.due_date,

        created_at=datetime.utcnow(),

        is_active=True
    )

    db.add(debt)
    db.commit()
    db.refresh(debt)

    return {
        "uuid": str(debt.uuid),
        "message": "Supplier debt added"
    }


# =====================================================
# GET SUPPLIER DETAILS
# =====================================================
@router.get("/{supplier_uuid}")
def get_supplier_details(
    supplier_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):

    supplier = (
        db.query(Supplier)
        .filter(
            Supplier.uuid == supplier_uuid,
            Supplier.user_id == current_user.id,
            Supplier.is_active == True
        )
        .first()
    )

    if not supplier:
        raise HTTPException(
            status_code=404,
            detail="Supplier not found"
        )

    debts = db.query(SupplierDebt).options(
        joinedload(SupplierDebt.payments)
    ).filter(
        SupplierDebt.supplier_id == supplier.id,
        SupplierDebt.user_id == current_user.id,
        SupplierDebt.is_active == True
    ).all()

    total_debt = 0
    overdue = 0

    debt_list = []

    for debt in debts:

        total_paid = sum(p.amount for p in debt.payments)

        remaining = debt.amount - total_paid

        total_debt += remaining

        if (
            debt.due_date and
            debt.due_date < datetime.utcnow() and
            remaining > 0
        ):
            overdue += remaining

        debt_list.append({
    "uuid": str(debt.uuid),

    "item_name": debt.item_name,

    "amount": debt.amount,

    "remaining": remaining,

    "paid": total_paid,

    "is_paid": remaining <= 0,

    "supplied_date": debt.supplied_date,

    "due_date": debt.due_date,

    "payments": [
        {
            "uuid": str(payment.uuid),

            "amount": payment.amount,

            "transaction_code": payment.transaction_code,

            "payment_date": payment.payment_date,

            "created_at": payment.created_at
        }
        for payment in debt.payments
    ]
})

    return {
        "uuid": str(supplier.uuid),

        "business_name": supplier.business_name,

        "paybill": supplier.paybill,
        "account_number": supplier.account_number,

        "phone": supplier.phone,

        "total_debt": total_debt,
        "overdue": overdue,

        "debts": debt_list
    }


@router.post("/debts/{debt_uuid}/payments")
def add_supplier_payment(
    debt_uuid: str,
    data: SupplierPaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_active_user
    )
):

    # =====================================================
    # GET DEBT
    # =====================================================
    debt = db.query(
        SupplierDebt
    ).options(
        joinedload(SupplierDebt.payments)
    ).filter(

        SupplierDebt.uuid == debt_uuid,

        SupplierDebt.user_id
            == current_user.id,

        SupplierDebt.is_active == True

    ).first()

    if not debt:

        raise HTTPException(

            status_code=404,

            detail="Supplier debt not found"
        )

    
    existing_uuid = db.query(
        SupplierPayment
    ).filter(

        SupplierPayment.uuid == data.uuid

    ).first()

    if existing_uuid:

        return {

            "payment": {

                "uuid":
                    str(existing_uuid.uuid),

                "amount":
                    existing_uuid.amount,

                "transaction_code":
                    existing_uuid.transaction_code,

                "payment_date":
                    existing_uuid.payment_date,

                "created_at":
                    existing_uuid.created_at,
            },

            "remaining_balance":
                0
        }

    # =====================================================
    # PREVENT DUPLICATE TRANSACTION CODE
    # =====================================================
    existing_code = db.query(
        SupplierPayment
    ).filter(

        SupplierPayment.transaction_code
            == data.transaction_code,

        SupplierPayment.user_id
            == current_user.id

    ).first()

    if existing_code:

        raise HTTPException(

            status_code=400,

            detail=
                "Transaction code already exists"
        )

    # =====================================================
    # CALCULATE REMAINING
    # =====================================================
    total_paid = sum(
        p.amount for p in debt.payments
    )

    remaining = (
        debt.amount - total_paid
    )

    # =====================================================
    # VALIDATE AMOUNT
    # =====================================================
    if (
        data.amount <= 0 or
        data.amount > remaining
    ):

        raise HTTPException(

            status_code=400,

            detail=
                f"Amount must be > 0 and <= {remaining}"
        )

    # =====================================================
    # CREATE PAYMENT
    # =====================================================
    payment = SupplierPayment(

        uuid=data.uuid,

        supplier_debt_id=debt.id,

        user_id=current_user.id,

        amount=data.amount,

        transaction_code=
            data.transaction_code,

        payment_date=
            data.payment_date
            or datetime.utcnow(),

        created_at=datetime.utcnow()
    )

    db.add(payment)

    db.commit()

    db.refresh(payment)

    # =====================================================
    # RETURN
    # =====================================================
    return {

        "payment": {

            "uuid":
                str(payment.uuid),

            "amount":
                payment.amount,

            "transaction_code":
                payment.transaction_code,

            "payment_date":
                payment.payment_date,

            "created_at":
                payment.created_at,
        },

        "remaining_balance":
            remaining - data.amount
    }



@router.delete("/debts/{debt_uuid}")
def delete_supplier_debt(
    debt_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):

    debt = db.query(SupplierDebt).filter(
        SupplierDebt.uuid == debt_uuid,
        SupplierDebt.user_id == current_user.id,
        SupplierDebt.is_active == True
    ).first()

    if not debt:
        raise HTTPException(
            status_code=404,
            detail="Supplier debt not found"
        )

    total_paid = db.query(
        func.coalesce(func.sum(SupplierPayment.amount), 0)
    ).filter(
        SupplierPayment.supplier_debt_id == debt.id,
        SupplierPayment.user_id == current_user.id
    ).scalar()

    remaining = debt.amount - total_paid

    # must be fully paid first
    if remaining != 0:
        raise HTTPException(
            status_code=400,
            detail="Supplier debt must be fully paid before deletion"
        )

    
    
    db.query(SupplierPayment).filter(
        SupplierPayment.supplier_debt_id == debt.id,
        SupplierPayment.user_id == current_user.id
    ).delete()

    # delete debt
    db.delete(debt)

    db.commit()

    return {
        "message": "Supplier debt and payments deleted permanently"
    }    