from pydantic import BaseModel

from src.products.schemas import ProductOut


class CartItemOut(BaseModel):
    id: int
    quantity: int
    product: ProductOut
