from sqlalchemy import select
from sqlalchemy.orm import Session

from src.cart.models import CartItem


class CartRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_items(self, user_id: int) -> list[CartItem]:
        return list(self.db.scalars(select(CartItem).where(CartItem.user_id == user_id)))

    def add_item(self, user_id: int, product_id: int, quantity: int = 1) -> CartItem:
        existing = self.db.scalar(
            select(CartItem).where(CartItem.user_id == user_id, CartItem.product_id == product_id)
        )
        if existing:
            existing.quantity += quantity
            self.db.flush()
            return existing

        item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
        self.db.add(item)
        self.db.flush()
        return item
