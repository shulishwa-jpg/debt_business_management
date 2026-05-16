from pydantic import BaseModel, EmailStr
from datetime import date
from typing import List
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class RegisterSchema(BaseModel):
    email: EmailStr
    password: str
    business_name: str


class LoginSchema(BaseModel):
    email: EmailStr
    password: str


class CustomerSchema(BaseModel):
    name: str
    phone: str | None = None


class DebtSchema(BaseModel):

    description: str
    amount: float
    due_date: date


class DashboardSchema(BaseModel):
    total_debts: float
    overdue_debts: float


from pydantic import BaseModel


class RegisterRequest(BaseModel):
    phone: str
    password: str
    business_name: str


class LoginRequest(BaseModel):
    phone: str
    password: str


from pydantic import BaseModel
from datetime import datetime


class SubscriptionCreate(BaseModel):
    user_id: int
    plan_name: str
    duration_days: int


class SubscriptionResponse(BaseModel):
    uuid: str
    plan_name: str
    start_date: datetime
    end_date: datetime
    status: str

    class Config:
        from_attributes = True

class CustomerCreate(BaseModel):
    uuid: str  # 🔥 ADD THIS
    name: str
    phone: str | None = None
    address: str | None = None


class CustomerUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    address: str | None = None


from uuid import UUID

class CustomerResponse(BaseModel):
    uuid: UUID  # ✅ instead of str
    name: str
    phone: str | None
    address: str | None

    class Config:
        from_attributes = True


class PaymentResponse(BaseModel):
    uuid: str
    amount: float
    receipt_number: str
    payment_date: datetime

    class Config:
        from_attributes = True


class DebtResponse(BaseModel):
    uuid: str
    description: str | None
    amount: float
    paid: float
    remaining: float
    taken_date: datetime | None
    due_date: datetime

    class Config:
        from_attributes = True


from pydantic import BaseModel
from datetime import date


from datetime import datetime

class DebtCreate(BaseModel):
    uuid: str  # 🔥 ADD THIS
    item: str
    amount: float
    taken_date: datetime | None = None
    due_date: datetime

# =========================
# PAYMENT SCHEMAS
# =========================
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PaymentCreate(BaseModel):
    uuid: str  # 🔥 ADD THIS
    amount: float
    receipt_number: str
    payment_date: Optional[datetime] = None


from pydantic import BaseModel

class ResetPasswordRequest(BaseModel):
    phone: str
    business_name: str
    new_password: str
    confirm_password: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    uuid: str
    phone: str
    business_name: str        



# =========================
# SUPPLIER SCHEMAS
# =========================

class SupplierCreate(BaseModel):
    uuid: str
    business_name: str

    paybill: str | None = None
    account_number: str | None = None

    phone: str | None = None
    address: str | None = None


class SupplierUpdate(BaseModel):
    business_name: str | None = None

    paybill: str | None = None
    account_number: str | None = None

    phone: str | None = None
    address: str | None = None


class SupplierResponse(BaseModel):
    uuid: str

    business_name: str

    paybill: str | None = None
    account_number: str | None = None

    phone: str | None = None
    address: str | None = None

    created_at: datetime

    class Config:
        from_attributes = True


# =========================
# SUPPLIER DEBT SCHEMAS
# =========================

class SupplierDebtCreate(BaseModel):
    uuid: str

    item_name: str

    amount: float

    supplied_date: datetime

    due_date: datetime | None = None


class SupplierDebtResponse(BaseModel):
    uuid: str

    item_name: str

    amount: float

    supplied_date: datetime

    due_date: datetime | None = None

    created_at: datetime

    class Config:
        from_attributes = True


# =========================
# SUPPLIER PAYMENT SCHEMAS
# =========================

class SupplierPaymentCreate(BaseModel):
    uuid: str

    amount: float

    transaction_code: str | None = None

    payment_date: datetime | None = None


class SupplierPaymentResponse(BaseModel):
    uuid: str

    amount: float

    transaction_code: str | None = None

    payment_date: datetime

    created_at: datetime

    class Config:
        from_attributes = True


# =========================
# PRODUCT
# ========================


# =========================
# PRODUCT
# =========================

class ProductCreate(BaseModel):

    uuid: str

    name: str

    category: Optional[str] = None

    barcode: Optional[str] = None

    base_unit: Optional[str] = None

    stock_quantity: float = 0

    min_stock: float = 0

    buying_price: float = 0

    selling_price: float = 0

    wholesale_price: float = 0

    wholesale_min_qty: float = 1

    pieces_per_carton: float = 1

    allow_flexible_amount: bool = False

    quick_quantities: List[float] = []

    sales_count: int = 0


class ProductResponse(BaseModel):

    uuid: str

    name: str

    category: Optional[str]

    barcode: Optional[str]

    base_unit: Optional[str]

    stock_quantity: float

    min_stock: float

    buying_price: float

    selling_price: float

    wholesale_price: float

    wholesale_min_qty: float

    pieces_per_carton: float

    allow_flexible_amount: bool

    quick_quantities: List[float]

    sales_count: int

    created_at: datetime

    class Config:
        from_attributes = True



# =========================
# SALE ITEM
# =========================
class SaleItemCreate(BaseModel):

    product_uuid: str

    quantity: float

    unit_type: Optional[str] = None

    price_used: float

    subtotal: float





# =========================
# SALE
# =========================
class SaleCreate(BaseModel):

    uuid: str

    customer_uuid: Optional[str] = None

    payment_method: str

    mpesa_code: Optional[str] = None

    total_amount: float

    items: List[SaleItemCreate]


class SaleResponse(BaseModel):

    uuid: str

    total_amount: float

    payment_method: str

    mpesa_code: Optional[str]

    created_at: datetime

    is_voided: bool

    class Config:
        from_attributes = True




# =========================
# STOCK ENTRY ITEM
# =========================
class StockEntryItemCreate(BaseModel):

    product_uuid: str

    quantity: float

    buying_price: float

    selling_price: float

    subtotal: float



# =========================
# STOCK ENTRY
# =========================
class StockEntryCreate(BaseModel):

    uuid: str

    supplier_uuid: Optional[str] = None

    invoice_number: Optional[str] = None

    total_amount: float

    amount_paid: float = 0

    payment_method: Optional[str] = None

    items: List[StockEntryItemCreate]


class StockEntryResponse(BaseModel):

    uuid: str

    invoice_number: Optional[str]

    total_amount: float

    amount_paid: float

    payment_method: Optional[str]

    created_at: datetime

    class Config:
        from_attributes = True



# =========================
# EXPENSE
# =========================
class ExpenseCreate(BaseModel):

    uuid: str

    title: str

    category: Optional[str] = None

    amount: float

    payment_method: Optional[str] = None


class ExpenseResponse(BaseModel):

    uuid: str

    title: str

    category: Optional[str]

    amount: float

    payment_method: Optional[str]

    created_at: datetime

    class Config:
        from_attributes = True


