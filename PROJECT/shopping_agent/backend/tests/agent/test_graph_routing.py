from src.agent import nodes


def test_route_after_search_retries_once_when_empty():
    assert nodes.route_after_search({"products": [], "retried": False}) == "retry_search"


def test_route_after_search_stops_retry_when_already_retried():
    assert nodes.route_after_search({"products": [], "retried": True}) == "rank_and_respond"


def test_route_after_search_goes_straight_through_when_found():
    assert nodes.route_after_search({"products": [{"id": 1}], "retried": False}) == "rank_and_respond"


def test_retry_search_falls_back_to_first_keyword():
    state = {"query": "저렴한 캠핑 의자 추천", "keywords": ["캠핑", "의자"]}
    result = nodes.retry_search(state)
    assert result["retried"] is True
    assert all(p["category"] for p in result["products"])
