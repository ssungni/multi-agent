from pydantic import BaseModel

from src.products.schemas import ProductOut


class ChatRequest(BaseModel):
    message: str
    thread_id: str | None = None


class ConfirmRequest(BaseModel):
    thread_id: str
    product_id: int | None = None
    confirm: bool


class ChatResponse(BaseModel):
    thread_id: str
    message: str
    products: list[ProductOut]
    awaiting_confirmation: bool
    added_product_id: int | None = None
