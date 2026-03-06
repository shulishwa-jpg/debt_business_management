from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, subscription, customers, debts, dashboard, mpesa

app = FastAPI()

# ✅ ADD CORS FIRST
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ THEN INCLUDE ROUTERS
app.include_router(mpesa.router)
app.include_router(auth.router)
app.include_router(subscription.router)
app.include_router(customers.router)
app.include_router(debts.router)
app.include_router(dashboard.router)

@app.get("/")
def root():
    return {"message": "Debt App API Running"}


# Health check endpoint for Railway
@app.get("/health")
def health_check():
    return {"status": "ok"}
