import uuid
from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


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