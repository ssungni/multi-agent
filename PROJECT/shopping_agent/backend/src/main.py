import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from src.agent.router import router as agent_router
from src.auth.router import router as auth_router
from src.auth.router import users_router
from src.cart.router import router as cart_router
from src.core.config import settings
from src.core.database import Base, engine
from src.exceptions import register_exception_handlers
from src.products.router import router as products_router

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS citext"))
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="CartMate Auth API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(products_router, prefix="/api")
app.include_router(cart_router, prefix="/api")
app.include_router(agent_router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}
