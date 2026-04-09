from pydantic import BaseModel, EmailStr
from datetime import date
from typing import List


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