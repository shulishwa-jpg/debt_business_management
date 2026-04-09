
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.database import engine
from app import models

from app.routers import auth, subscription, customers, debts, dashboard, mpesa

app = FastAPI()

# ================= CREATE TABLES =================
models.Base.metadata.create_all(bind=engine)

# ================= 🔥 AUTO ADD UUID COLUMNS =================
def add_uuid_columns():
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS uuid TEXT"))
        conn.execute(text("ALTER TABLE customers ADD COLUMN IF NOT EXISTS uuid TEXT"))
        conn.execute(text("ALTER TABLE debts ADD COLUMN IF NOT EXISTS uuid TEXT"))
        conn.execute(text("ALTER TABLE payments ADD COLUMN IF NOT EXISTS uuid TEXT"))
        conn.execute(text("ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS uuid TEXT"))
        conn.commit()

# 🔥 RUN ON STARTUP
add_uuid_columns()


# ================= CORS =================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= ROUTERS =================
app.include_router(mpesa.router)
app.include_router(auth.router)
app.include_router(subscription.router)
app.include_router(customers.router)
app.include_router(debts.router)
app.include_router(dashboard.router)
