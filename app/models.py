import uuid
from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base

from sqlalchemy import JSON

from sqlalchemy import Boolean

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
)


# =========================
# USER
# =========================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))

    phone = Column(String, unique=True, index=True, nullable=False)
    password = Column(String)
    business_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    customers = relationship("Customer", back_populates="user")
    subscription = relationship("Subscription", uselist=False, back_populates="user")


# =========================
# SUBSCRIPTION
# =========================
class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))

    user_id = Column(Integer, ForeignKey("users.id"))
    plan_name = Column(String)
    start_date = Column(DateTime, default=func.now())
    end_date = Column(DateTime)
    status = Column(String, default="active")

    user = relationship("User", back_populates="subscription")


# =========================
# CUSTOMER
# =========================
class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))

    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="customers")

    notifications = relationship(
        "Notification",
        back_populates="customer",
        cascade="all, delete-orphan"
    )


# =========================
# DEBT
# =========================
class Debt(Base):
    __tablename__ = "debts"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))

    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), index=True)

    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    taken_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    user = relationship("User")
    customer = relationship("Customer")

    payments = relationship("Payment", back_populates="debt")


# =========================
# PAYMENT
# =========================
class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))

    debt_id = Column(Integer, ForeignKey("debts.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)

    amount = Column(Float, nullable=False)
    receipt_number = Column(String, unique=True, index=True)
    payment_date = Column(DateTime, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    debt = relationship("Debt", back_populates="payments")
    user = relationship("User")


# ========================= 
# NOTIFICATION
# =========================
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))

    message = Column(String, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"))

    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer", back_populates="notifications")



# =========================
# SUPPLIER
# =========================
class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))

    user_id = Column(Integer, ForeignKey("users.id"), index=True)

    business_name = Column(String, nullable=False)

    paybill = Column(String, nullable=True)
    account_number = Column(String, nullable=True)

    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    is_active = Column(Boolean, default=True)

    user = relationship("User")

    supplier_debts = relationship(
        "SupplierDebt",
        back_populates="supplier",
        cascade="all, delete-orphan"
    )


# =========================
# SUPPLIER DEBT
# =========================
class SupplierDebt(Base):
    __tablename__ = "supplier_debts"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))

    supplier_id = Column(Integer, ForeignKey("suppliers.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)

    item_name = Column(String, nullable=False)

    amount = Column(Float, nullable=False)

    supplied_date = Column(DateTime, nullable=False)

    # optional because many suppliers don't force deadline
    due_date = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    is_active = Column(Boolean, default=True)

    supplier = relationship("Supplier", back_populates="supplier_debts")

    payments = relationship(
        "SupplierPayment",
        back_populates="supplier_debt",
        cascade="all, delete-orphan"
    )


# =========================
# SUPPLIER PAYMENT
# =========================
class SupplierPayment(Base):
    __tablename__ = "supplier_payments"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))

    supplier_debt_id = Column(
        Integer,
        ForeignKey("supplier_debts.id"),
        index=True
    )

    user_id = Column(Integer, ForeignKey("users.id"), index=True)

    amount = Column(Float, nullable=False)

    transaction_code = Column(String, nullable=True)

    payment_date = Column(DateTime, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    supplier_debt = relationship(
        "SupplierDebt",
        back_populates="payments"
    )


class Product(Base):
    __tablename__ = "products"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    uuid = Column(
        String,
        unique=True,
        index=True,
        default=lambda: str(uuid.uuid4())
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        index=True
    )

    # =========================
    # PRODUCT INFO
    # =========================

    name = Column(
        String,
        index=True,
        nullable=False
    )

    category = Column(
        String,
        index=True,
        nullable=True
    )

    barcode = Column(
        String,
        unique=True,
        index=True,
        nullable=True
    )

    base_unit = Column(
        String,
        nullable=True
    )

    # =========================
    # STOCK
    # =========================

    stock_quantity = Column(
        Float,
        index=True,
        default=0
    )

    min_stock = Column(
        Float,
        default=0
    )

    # =========================
    # PRICES
    # =========================

    buying_price = Column(
        Float,
        default=0
    )

    selling_price = Column(
        Float,
        default=0
    )

    wholesale_price = Column(
        Float,
        default=0
    )

    wholesale_min_qty = Column(
        Float,
        default=1
    )

    # =========================
    # FLEXIBLE SALES
    # =========================

    allow_flexible_amount = Column(
        Boolean,
        default=False
    )

    # =========================
    # UNITS / QUICK QTY
    # =========================

    pieces_per_carton = Column(
        Float,
        default=1
    )

    quick_quantities = Column(
        JSON,
        default=list
    )

    # =========================
    # ANALYTICS
    # =========================

    sales_count = Column(
        Integer,
        default=0,
        index=True
    )

    # =========================
    # SYSTEM
    # =========================

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        index=True
    )

    is_active = Column(
        Boolean,
        index=True,
        default=True
    )

    # =========================
    # RELATIONSHIPS
    # =========================

    user = relationship("User")

    sale_items = relationship(
        "SaleItem",
        back_populates="product"
    )

    stock_items = relationship(
        "StockEntryItem",
        back_populates="product"
    )


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True)

    uuid = Column(
        String,
        unique=True,
        index=True,
        default=lambda: str(uuid.uuid4())
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        index=True
    )

    # optional customer for credit
    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=True,
        index=True
    )

    total_amount = Column(
        Float,
        nullable=False
    )

    payment_method = Column(
        String,
        nullable=False
    )  # CASH / MPESA / CREDIT

    mpesa_code = Column(
        String,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        index=True
    )
    
    is_voided = Column(
        Boolean,
        default=False
    )

    user = relationship("User")

    customer = relationship("Customer")

    items = relationship(
        "SaleItem",
        back_populates="sale",
        cascade="all, delete-orphan"
    )


class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True)

    uuid = Column(
        String,
        unique=True,
        index=True,
        default=lambda: str(uuid.uuid4())
    )

    sale_id = Column(
        Integer,
        ForeignKey("sales.id"),
        index=True
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        index=True
    )

    quantity = Column(
        Float,
        nullable=False
    )

    unit_type = Column(
        String,
        nullable=True
    )  # piece / half / quarter / carton

    price_used = Column(
        Float,
        nullable=False
    )

    subtotal = Column(
        Float,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    sale = relationship(
        "Sale",
        back_populates="items"
    )

    product = relationship(
        "Product",
        back_populates="sale_items"
    )



class StockEntry(Base):
    __tablename__ = "stock_entries"

    id = Column(Integer, primary_key=True)

    uuid = Column(
        String,
        unique=True,
        index=True,
        default=lambda: str(uuid.uuid4())
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        index=True
    )

    supplier_id = Column(
        Integer,
        ForeignKey("suppliers.id"),
        nullable=True,
        index=True
    )

    invoice_number = Column(
        String,
        nullable=True
    )

    total_amount = Column(
        Float,
        default=0
    )

    amount_paid = Column(
        Float,
        default=0
    )

    payment_method = Column(
        String,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        index=True
    )

    user = relationship("User")

    supplier = relationship("Supplier")

    items = relationship(
        "StockEntryItem",
        back_populates="stock_entry",
        cascade="all, delete-orphan"
    )


class StockEntryItem(Base):
    __tablename__ = "stock_entry_items"

    id = Column(Integer, primary_key=True)

    uuid = Column(
        String,
        unique=True,
        index=True,
        default=lambda: str(uuid.uuid4())
    )

    stock_entry_id = Column(
        Integer,
        ForeignKey("stock_entries.id"),
        index=True
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        index=True
    )

    quantity = Column(
        Float,
        nullable=False
    )

    buying_price = Column(
        Float,
        nullable=False
    )

    selling_price = Column(
        Float,
        nullable=False
    )

    subtotal = Column(
        Float,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    stock_entry = relationship(
        "StockEntry",
        back_populates="items"
    )

    product = relationship(
        "Product",
        back_populates="stock_items"
    )


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True)

    uuid = Column(
        String,
        unique=True,
        index=True,
        default=lambda: str(uuid.uuid4())
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        index=True
    )

    title = Column(
        String,
        nullable=False
    )

    category = Column(
        String,
        nullable=True
    )

    amount = Column(
        Float,
        nullable=False
    )

    payment_method = Column(
        String,
        nullable=True
    )

    is_deleted = Column(
        Boolean,
        default=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        index=True
    )

    user = relationship("User")




