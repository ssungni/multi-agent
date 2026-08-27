from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.auth.dependencies import get_current_user
from src.auth.models import User
from src.cart.repository import CartRepository
from src.cart.schemas import CartItemOut
from src.core.database import get_db
from src.products import repository as product_repository

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("", response_model=list[CartItemOut])
def get_cart(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = CartRepository(db).list_items(user.id)
    return [
        CartItemOut(id=item.id, quantity=item.quantity, product=product_repository.get_product(item.product_id))
        for item in items
        if product_repository.get_product(item.product_id) is not None
    ]
