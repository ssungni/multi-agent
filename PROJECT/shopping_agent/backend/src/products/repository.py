from src.products.seed_data import CATEGORIES, PRODUCTS


def get_categories() -> list[str]:
    return CATEGORIES


def get_product(product_id: int) -> dict | None:
    return next((p for p in PRODUCTS if p["id"] == product_id), None)


def search_products(
    query: str | None = None,
    category: str | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
    limit: int = 5,
) -> list[dict]:
    """키워드 스코어링 + 필터 기반 mock 검색. 실 API 붙일 때 이 함수만 교체하면 됨."""
    results = PRODUCTS

    if category:
        results = [p for p in results if p["category"] == category]
    if min_price is not None:
        results = [p for p in results if p["price"] >= min_price]
    if max_price is not None:
        results = [p for p in results if p["price"] <= max_price]

    if query:
        keywords = [kw.strip() for kw in query.lower().split() if kw.strip()]

        def score(p: dict) -> int:
            haystack = (p["name"] + " " + p["brand"] + " " + " ".join(p["tags"])).lower()
            return sum(haystack.count(kw) for kw in keywords)

        scored = [(score(p), p) for p in results]
        results = [p for s, p in scored if s > 0]
        results.sort(key=lambda p: (score(p), p["rating"]), reverse=True)
    else:
        results = sorted(results, key=lambda p: p["rating"], reverse=True)

    return results[:limit]
