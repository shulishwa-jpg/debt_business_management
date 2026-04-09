
import uuid
from app.database import SessionLocal
from app.models import User, Customer, Debt, Payment, Subscription

db = SessionLocal()

def backfill_uuid(model, name):
    items = db.query(model).all()
    count = 0

    for item in items:
        if not item.uuid:
            item.uuid = str(uuid.uuid4())
            count += 1

    db.commit()
    print(f"✅ {name}: updated {count} records")


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
