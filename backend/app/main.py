from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.constants import MAX_REQUEST_BODY_BYTES
from app.database import Base, SessionLocal, engine
from app.routers import auth, chat, dashboard, expenses, income, ocr, profile, transactions
from app import crud


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        crud.seed_db(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Spendly API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def limit_request_body_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length is not None and int(content_length) > MAX_REQUEST_BODY_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Request body too large.")
    return await call_next(request)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(expenses.router)
app.include_router(income.router)
app.include_router(transactions.router)
app.include_router(ocr.router)
app.include_router(profile.router)
app.include_router(chat.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
