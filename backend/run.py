from fastapi import FastAPI
from app.routes.scheme_routes import router as scheme_router

app = FastAPI(title="SchemeHouse AI")

app.include_router(scheme_router)

@app.get("/")
def home():
    return {"message": "SchemeHouse Backend Running"}