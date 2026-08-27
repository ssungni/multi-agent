from fastapi import APIRouter, HTTPException

from src.products import repository
from src.products.schemas import ProductOut

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductOut])
def list_products(
    q: str | None = None,
    category: str | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
    limit: int = 20,
):
    return repository.search_products(q, category, min_price, max_price, limit)


@router.get("/categories", response_model=list[str])
def list_categories():
    return repository.get_categories()


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int):
    product = repository.get_product(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
