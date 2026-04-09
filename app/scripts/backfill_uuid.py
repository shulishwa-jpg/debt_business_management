
from sqlalchemy import text

# 🔥 ADD THIS FUNCTION
def add_uuid_columns():
    print("🔧 Adding uuid columns if missing...")

    db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS uuid TEXT"))
    db.execute(text("ALTER TABLE customers ADD COLUMN IF NOT EXISTS uuid TEXT"))
    db.execute(text("ALTER TABLE debts ADD COLUMN IF NOT EXISTS uuid TEXT"))
    db.execute(text("ALTER TABLE payments ADD COLUMN IF NOT EXISTS uuid TEXT"))
    db.execute(text("ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS uuid TEXT"))

    db.commit()

    print("✅ UUID columns ensured")


def run():
    print("🚀 Starting UUID backfill...\n")

    # 🔥 ADD THIS LINE
    add_uuid_columns()

    backfill_uuid(User, "Users")
    backfill_uuid(Customer, "Customers")
    backfill_uuid(Debt, "Debts")
    backfill_uuid(Payment, "Payments")
    backfill_uuid(Subscription, "Subscriptions")

    print("\n🎉 Done!")

import uuid
from app.database import SessionLocal
from app.models import User, Customer, Debt, Payment, Subscription

db = SessionLocal()

def backfill_uuid(model, name):
    print(f"🔄 Processing {name}...")

    count = 0

    # 🔥 use batching instead of .all()
    items = db.query(model).yield_per(100)

    for item in items:
        if not item.uuid:
            item.uuid = str(uuid.uuid4())
            count += 1

            # commit in chunks
            if count % 100 == 0:
                db.commit()
                print(f"   {name}: updated {count}...")

    db.commit()
    print(f"✅ {name}: updated {count}")


def run():
    print("🚀 Starting UUID backfill...\n")

    backfill_uuid(User, "Users")
    backfill_uuid(Customer, "Customers")
    backfill_uuid(Debt, "Debts")
    backfill_uuid(Payment, "Payments")
    backfill_uuid(Subscription, "Subscriptions")

    print("\n🎉 Done!")


if __name__ == "__main__":
    run()
