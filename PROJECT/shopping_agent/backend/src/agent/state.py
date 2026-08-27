from typing import TypedDict


class ChatState(TypedDict, total=False):
    query: str
    keywords: list[str]
    category: str | None
    min_price: int | None
    max_price: int | None
    products: list[dict]
    retried: bool
    response: str
    added_product_id: int | None
