from src.products import repository


def test_search_by_keyword_matches_name_and_tag():
    results = repository.search_products(query="이어폰")
    assert results
    assert all("이어폰" in r["name"] or "이어폰" in r["tags"] for r in results)


def test_search_filters_by_category_and_price():
    results = repository.search_products(category="식품", max_price=10000)
    assert results
    assert all(r["category"] == "식품" and r["price"] <= 10000 for r in results)


def test_search_no_match_returns_empty():
    assert repository.search_products(query="존재하지않는상품명xyz") == []


def test_search_without_query_returns_top_rated():
    results = repository.search_products(limit=3)
    ratings = [r["rating"] for r in results]
    assert ratings == sorted(ratings, reverse=True)


def test_get_product_by_id():
    assert repository.get_product(1) is not None
    assert repository.get_product(99999) is None
