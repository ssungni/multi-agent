from pydantic import BaseModel


class ProductOut(BaseModel):
    id: int
    name: str
    category: str
    brand: str
    price: int
    stock: int
    rating: float
    review_count: int
    tags: list[str]
