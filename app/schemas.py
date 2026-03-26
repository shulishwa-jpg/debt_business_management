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
    id: int
    user_id: int
    plan_name: str
    start_date: datetime
    end_date: datetime
    status: str

    class Config:
        from_attributes = True

class CustomerCreate(BaseModel):
    name: str
    phone: str | None = None
    address: str | None = None


class CustomerUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    address: str | None = None


class CustomerResponse(BaseModel):
    id: int
    user_id: int
    name: str
    phone: str | None
    address: str | None

    class Config:
        from_attributes = True



class DebtResponse(BaseModel):
    id: int
    customer_id: int
    description: str | None
    amount: float
    paid: float
    remaining: float
    taken_date: date | None
    due_date: date

    class Config:
        from_attributes = True


from pydantic import BaseModel
from datetime import date


from datetime import datetime

class DebtCreate(BaseModel):
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
    amount: float
    receipt_number: str
    payment_date: Optional[datetime] = None  # Optional, defaults to now in backend


from pydantic import BaseModel

class ResetPasswordRequest(BaseModel):
    phone: str
    business_name: str
    new_password: str
    confirm_password: str

