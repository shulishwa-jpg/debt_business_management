from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.database import get_db

from app.models import (
    User,
    Customer,
    Debt,
    Product,
    Sale,
    SaleItem,
    StockEntry,
    StockEntryItem,
    Expense,
)

from app.schemas import (
    ProductCreate,
    SaleCreate,
    StockEntryCreate,
    ExpenseCreate,
)

from app.security import get_current_active_user


router = APIRouter(
    prefix="/pos",
    tags=["POS"]
)


# =====================================================
# PRODUCTS
# =====================================================

@router.post("/products")
def create_product(

    data: ProductCreate,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_active_user
    )
):

    # ================= CHECK EXISTING =================

    existing = db.query(Product).filter(

        Product.user_id ==
            current_user.id,

        Product.name ==
            data.name,

        Product.is_active == True
    ).first()

    if existing:

        raise HTTPException(

            status_code=400,

            detail=
                "Product already exists"
        )

    # ================= CREATE PRODUCT =================

    product = Product(

        uuid=data.uuid,

        user_id=current_user.id,

        name=data.name,

        category=data.category,

        barcode=data.barcode,

        base_unit=data.base_unit,

        stock_quantity=
            data.stock_quantity,

        min_stock=
            data.min_stock,

        buying_price=
            data.buying_price,

        selling_price=
            data.selling_price,

        wholesale_price=
            data.wholesale_price,

        wholesale_min_qty=
            data.wholesale_min_qty,

        pieces_per_carton=
            data.pieces_per_carton,

        allow_flexible_amount=
            data.allow_flexible_amount,

        quick_quantities=
            data.quick_quantities,

        sales_count=
            data.sales_count,
    )

    db.add(product)

    db.commit()

    db.refresh(product)

    # ================= RESPONSE =================

    return {

        "message":
            "Product created",

        "uuid":
            product.uuid,
    }


# =====================================================
# GET PRODUCTS
# =====================================================

@router.get("/products")
def get_products(

    search: str = "",

    low_stock: bool = False,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_active_user
    )
):

    query = db.query(Product).filter(

        Product.user_id ==
            current_user.id,

        Product.is_active == True
    )

    # ================= SEARCH =================

    if search:

        query = query.filter(
            Product.name.ilike(
                f"%{search}%"
            )
        )

    # ================= SORT =================
    # FAST SELLING FIRST

    products = query.order_by(

        Product.sales_count.desc(),

        Product.name.asc(),
    ).all()

    result = []

    for p in products:

        # ================= LOW STOCK FILTER =================

        if low_stock:

            if p.stock_quantity > p.min_stock:
                continue

        result.append({

            "uuid":
                str(p.uuid),

            "name":
                p.name,

            "category":
                p.category,

            "barcode":
                p.barcode,

            "base_unit":
                p.base_unit,

            "stock_quantity":
                p.stock_quantity,

            "min_stock":
                p.min_stock,

            "buying_price":
                p.buying_price,

            "selling_price":
                p.selling_price,

            "wholesale_price":
                p.wholesale_price,

            "wholesale_min_qty":
                p.wholesale_min_qty,

            "pieces_per_carton":
                p.pieces_per_carton,

            "allow_flexible_amount":
                p.allow_flexible_amount,

            "quick_quantities":
                p.quick_quantities,

            "sales_count":
                p.sales_count,
        })

    return result


# =====================================================
# UPDATE PRODUCT
# =====================================================

@router.put("/products/{product_uuid}")
def update_product(

    product_uuid: str,

    data: ProductCreate,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_active_user
    )
):

    product = db.query(Product).filter(

        Product.uuid == product_uuid,

        Product.user_id ==
            current_user.id,

        Product.is_active == True
    ).first()

    if not product:

        raise HTTPException(

            status_code=404,

            detail="Product not found"
        )

    product.name = data.name

    product.category = data.category

    product.barcode = data.barcode

    product.base_unit = data.base_unit

    product.stock_quantity = (
        data.stock_quantity
    )

    product.min_stock = (
        data.min_stock
    )

    product.buying_price = (
        data.buying_price
    )

    product.selling_price = (
        data.selling_price
    )

    product.wholesale_price = (
        data.wholesale_price
    )

    product.wholesale_min_qty = (
        data.wholesale_min_qty
    )

    product.pieces_per_carton = (
        data.pieces_per_carton
    )

    product.allow_flexible_amount = (
        data.allow_flexible_amount
    )

    product.quick_quantities = (
        data.quick_quantities
    )

    product.sales_count = (
        data.sales_count
    )

    db.commit()

    return {
        "message":
            "Product updated"
    }


# =====================================================
# DELETE PRODUCT
# =====================================================

@router.delete("/products/{product_uuid}")
def delete_product(
    product_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):

    product = db.query(Product).filter(
        Product.uuid == product_uuid,
        Product.user_id == current_user.id,
        Product.is_active == True
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    product.is_active = False

    db.commit()

    return {
        "message": "Product deleted"
    }


# =====================================================
# CREATE SALE
# =====================================================

@router.post("/sales")
def create_sale(
    data: SaleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):

    if len(data.items) == 0:
        raise HTTPException(
            status_code=400,
            detail="Cart is empty"
        )

    customer = None

    if data.customer_uuid:

        customer = db.query(Customer).filter(
            Customer.uuid == data.customer_uuid,
            Customer.user_id == current_user.id,
            Customer.is_active == True
        ).first()

        if not customer:
            raise HTTPException(
                status_code=404,
                detail="Customer not found"
            )

    sale = Sale(

        uuid=data.uuid,

        user_id=current_user.id,

        customer_id=
            customer.id if customer else None,

        total_amount=data.total_amount,

        payment_method=data.payment_method,

        mpesa_code=data.mpesa_code,
    )

    db.add(sale)

    db.flush()

    # ==========================================
    # ITEMS
    # ==========================================
    for item in data.items:

        product = db.query(Product).filter(
            Product.uuid == item.product_uuid,
            Product.user_id == current_user.id,
            Product.is_active == True
        ).first()

        if not product:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        # ======================================
        # STOCK VALIDATION
        # ======================================
        if item.quantity > product.stock_quantity:

            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {product.name}"
            )

        # reduce stock
        product.stock_quantity -= item.quantity

        product.sales_count += 1

        sale_item = SaleItem(

            sale_id=sale.id,

            product_id=product.id,

            quantity=item.quantity,

            unit_type=item.unit_type,

            price_used=item.price_used,

            subtotal=item.subtotal,
        )

        db.add(sale_item)

    # ==========================================
    # CREDIT SALE
    # ==========================================
    if data.payment_method == "CREDIT":

        if not customer:

            raise HTTPException(
                status_code=400,
                detail="Customer required for credit sale"
            )

        debt = Debt(

            user_id=current_user.id,

            customer_id=customer.id,

            description="POS Credit Sale",

            amount=data.total_amount,

            taken_date=datetime.utcnow(),

            due_date=datetime.utcnow(),
        )

        db.add(debt)

    db.commit()

    return {
        "message": "Sale completed",
        "sale_uuid": sale.uuid
    }


# =====================================================
# SALES HISTORY
# =====================================================

@router.get("/sales")
def get_sales(

    payment_method: str = "",

    today_only: bool = False,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_active_user
    )
):

    query = db.query(Sale).options(

        joinedload(Sale.items)
        .joinedload(SaleItem.product)

    ).filter(

        Sale.user_id ==
            current_user.id,

        Sale.is_voided == False
    )

    # =====================================================
    # FILTER PAYMENT METHOD
    # =====================================================

    if payment_method:

        query = query.filter(

            Sale.payment_method ==
                payment_method
        )

    # =====================================================
    # GET SALES
    # =====================================================

    sales = query.order_by(

        Sale.created_at.desc()

    ).all()

    result = []

    today = date.today()

    # =====================================================
    # BUILD RESPONSE
    # =====================================================

    for s in sales:

        # TODAY FILTER

        if today_only:

            if s.created_at.date() != today:
                continue

        result.append({

            "uuid":
                str(s.uuid),

            "total_amount":
                s.total_amount,

            "payment_method":
                s.payment_method,

            "mpesa_code":
                s.mpesa_code,

            "created_at":
                s.created_at,

            "items": [

                {

                    "product_name":

                        i.product.name

                        if i.product

                        else "Unknown Product",

                    "quantity":
                        i.quantity,

                    "unit_type":

                        i.unit_type

                        if i.unit_type

                        else "",

                    "price_used":
                        i.price_used,

                    "subtotal":
                        i.subtotal,
                }

                for i in s.items
            ]
        })

    return result


# =====================================================
# VOID SALE
# =====================================================

@router.post("/sales/{sale_uuid}/void")
def void_sale(

    sale_uuid: str,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_active_user
    )
):

    sale = db.query(Sale).options(

        joinedload(Sale.items)
        .joinedload(SaleItem.product)

    ).filter(

        Sale.uuid == sale_uuid,

        Sale.user_id ==
            current_user.id,

        Sale.is_voided == False

    ).first()

    # ==========================================
    # VALIDATE
    # ==========================================

    if not sale:

        raise HTTPException(

            status_code=404,

            detail=
                "Sale not found"
        )

    # ==========================================
    # RESTORE STOCK
    # ==========================================

    for item in sale.items:

        if item.product:

            item.product.stock_quantity += (
                item.quantity
            )

    # ==========================================
    # VOID SALE
    # ==========================================

    sale.is_voided = True

    db.commit()

    # ==========================================
    # RESPONSE
    # ==========================================

    return {

        "message":
            "Sale voided successfully"
    }



@router.delete("/expenses/{expense_uuid}")
def delete_expense(

    expense_uuid: str,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_active_user
    )
):

    expense = db.query(Expense).filter(

        Expense.uuid ==
            expense_uuid,

        Expense.user_id ==
            current_user.id,
    ).first()

    if not expense:

        raise HTTPException(

            status_code=404,

            detail="Expense not found"
        )

    expense.is_deleted = True

    db.commit()

    return {
        "message": "Expense deleted"
    }



# =====================================================
# STOCK ENTRY
# =====================================================

@router.post("/stock-entries")
def create_stock_entry(
    data: StockEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):

    stock_entry = StockEntry(

        uuid=data.uuid,

        user_id=current_user.id,

        invoice_number=data.invoice_number,

        total_amount=data.total_amount,

        amount_paid=data.amount_paid,

        payment_method=data.payment_method,
    )

    db.add(stock_entry)

    db.flush()

    # ==========================================
    # ITEMS
    # ==========================================
    for item in data.items:

        product = db.query(Product).filter(
            Product.uuid == item.product_uuid,
            Product.user_id == current_user.id,
            Product.is_active == True
        ).first()

        if not product:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        # increase stock
        product.stock_quantity += item.quantity

        # update prices
        product.buying_price = item.buying_price

        product.selling_price = item.selling_price

        stock_item = StockEntryItem(

            stock_entry_id=stock_entry.id,

            product_id=product.id,

            quantity=item.quantity,

            buying_price=item.buying_price,

            selling_price=item.selling_price,

            subtotal=item.subtotal,
        )

        db.add(stock_item)

    db.commit()

    return {
        "message": "Stock added"
    }


# =====================================================
# STOCK HISTORY
# =====================================================

@router.get("/stock-entries")
def get_stock_entries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):

    entries = db.query(StockEntry).options(
        joinedload(StockEntry.items)
    ).filter(
        StockEntry.user_id == current_user.id
    ).order_by(
        StockEntry.created_at.desc()
    ).all()

    result = []

    for e in entries:

        result.append({

            "uuid": str(e.uuid),

            "invoice_number":
                e.invoice_number,

            "total_amount":
                e.total_amount,

            "amount_paid":
                e.amount_paid,

            "payment_method":
                e.payment_method,

            "created_at":
                e.created_at,
        })

    return result


# =====================================================
# EXPENSES
# =====================================================

@router.post("/expenses")
def create_expense(
    data: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):

    expense = Expense(

        uuid=data.uuid,

        user_id=current_user.id,

        title=data.title,

        category=data.category,

        amount=data.amount,

        payment_method=data.payment_method,
    )

    db.add(expense)

    db.commit()

    return {
        "message": "Expense added"
    }


# =====================================================
# GET EXPENSES
# =====================================================

@router.get("/expenses")
def get_expenses(

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_active_user
    )
):

    expenses = db.query(Expense).filter(

        Expense.user_id ==
            current_user.id,

        Expense.is_deleted == False

    ).order_by(

        Expense.created_at.desc()

    ).all()

    return [

        {

            "uuid":
                str(e.uuid),

            "title":
                e.title,

            "category":
                e.category,

            "amount":
                e.amount,

            "payment_method":
                e.payment_method,

            "created_at":
                e.created_at,
        }

        for e in expenses
    ]


# =====================================================
# POS DASHBOARD
# =====================================================

@router.get("/dashboard")
def get_pos_dashboard(

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_active_user
    )
):

    today = date.today()

    # ==========================================
    # TODAY SALES
    # ==========================================

    sales_total = db.query(
        func.sum(Sale.total_amount)
    ).filter(

        Sale.user_id ==
            current_user.id,

        func.date(
            Sale.created_at
        ) == today,

        Sale.is_voided == False

    ).scalar() or 0

    # ==========================================
    # STOCK VALUE
    # ==========================================

    products = db.query(Product).filter(

        Product.user_id ==
            current_user.id,

        Product.is_active == True

    ).all()

    stock_value = 0

    low_stock = 0

    for p in products:

        stock_value += (

            p.stock_quantity *
            p.buying_price
        )

        if p.stock_quantity <= p.min_stock:

            low_stock += 1

    # ==========================================
    # EXPENSES
    # ==========================================

    expenses_total = db.query(
        func.sum(Expense.amount)
    ).filter(

        Expense.user_id ==
            current_user.id,

        func.date(
            Expense.created_at
        ) == today

    ).scalar() or 0

    # ==========================================
    # RESPONSE
    # ==========================================

    return {

        "today_sales":
            sales_total,

        "stock_value":
            stock_value,

        "today_expenses":
            expenses_total,

        "low_stock_items":
            low_stock,
    }