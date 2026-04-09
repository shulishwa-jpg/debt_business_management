
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.database import engine
from app import models

from app.routers import auth, subscription, customers, debts, dashboard, mpesa

app = FastAPI()

# ================= CREATE TABLES =================
models.Base.metadata.create_all(bind=engine)

# ================= 🔥 AUTO FIX DB =================
def setup_database():
    with engine.connect() as conn:
        # ✅ enable uuid generator
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))

        # ✅ add uuid columns
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS uuid TEXT"))
        conn.execute(text("ALTER TABLE customers ADD COLUMN IF NOT EXISTS uuid TEXT"))
        conn.execute(text("ALTER TABLE debts ADD COLUMN IF NOT EXISTS uuid TEXT"))
        conn.execute(text("ALTER TABLE payments ADD COLUMN IF NOT EXISTS uuid TEXT"))
        conn.execute(text("ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS uuid TEXT"))

        # ✅ fill missing uuid
        conn.execute(text("UPDATE users SET uuid = gen_random_uuid() WHERE uuid IS NULL"))
        conn.execute(text("UPDATE customers SET uuid = gen_random_uuid() WHERE uuid IS NULL"))
        conn.execute(text("UPDATE debts SET uuid = gen_random_uuid() WHERE uuid IS NULL"))
        conn.execute(text("UPDATE payments SET uuid = gen_random_uuid() WHERE uuid IS NULL"))
        conn.execute(text("UPDATE subscriptions SET uuid = gen_random_uuid() WHERE uuid IS NULL"))

        conn.commit()

# 🔥 RUN ON STARTUP
setup_database()


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
