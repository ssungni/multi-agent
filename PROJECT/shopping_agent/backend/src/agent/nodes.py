from langchain_anthropic import ChatAnthropic
from langgraph.types import interrupt
from pydantic import BaseModel, Field

from src.agent.state import ChatState
from src.cart.repository import CartRepository
from src.core.config import settings
from src.products import repository as product_repository
from src.products.seed_data import CATEGORIES

MODEL = "claude-haiku-4-5-20251001"

llm = ChatAnthropic(model=MODEL, api_key=settings.ANTHROPIC_API_KEY, timeout=30, max_retries=2)


class Intent(BaseModel):
    keywords: list[str] = Field(description="상품명/브랜드 등 검색에 쓸 핵심 키워드 (1~3개)")
    category: str | None = Field(default=None, description=f"다음 중 하나 또는 null: {CATEGORIES}")
    min_price: int | None = Field(default=None, description="원 단위 최소 가격, 언급 없으면 null")
    max_price: int | None = Field(default=None, description="원 단위 최대 가격, 언급 없으면 null")


intent_llm = llm.with_structured_output(Intent)


def extract_intent(state: ChatState) -> dict:
    intent: Intent = intent_llm.invoke(
        f"다음 쇼핑 요청에서 검색 조건을 추출해줘: {state['query']}"
    )
    return {
        "keywords": intent.keywords,
        "category": intent.category,
        "min_price": intent.min_price,
        "max_price": intent.max_price,
        "retried": False,
    }


def search_products(state: ChatState) -> dict:
    query = " ".join(state.get("keywords") or [])
    results = product_repository.search_products(
        query=query or None,
        category=state.get("category"),
        min_price=state.get("min_price"),
        max_price=state.get("max_price"),
    )
    return {"products": results}


def route_after_search(state: ChatState) -> str:
    if not state.get("products") and not state.get("retried"):
        return "retry_search"
    return "rank_and_respond"


def retry_search(state: ChatState) -> dict:
    fallback_keyword = (state.get("keywords") or [state["query"]])[0]
    results = product_repository.search_products(query=fallback_keyword)
    return {"products": results, "retried": True}


def rank_and_respond(state: ChatState) -> dict:
    products = state.get("products") or []
    if not products:
        return {"response": "조건에 맞는 상품을 찾지 못했어요. 다른 키워드로 다시 물어봐 주시겠어요?"}

    listing = "\n".join(
        f"- (id={p['id']}) {p['name']} / {p['brand']} / {p['price']:,}원 / 평점 {p['rating']} ({p['review_count']}개 리뷰)"
        for p in products
    )
    reply = llm.invoke(
        f"사용자 요청: {state['query']}\n\n검색된 상품 후보:\n{listing}\n\n"
        "위 후보 중 사용자 요청에 가장 잘 맞는 상품을 골라 2~3문장으로 자연스럽게 추천해줘. "
        "상품명과 가격을 반드시 언급하고, 장바구니에 담을지 물어보는 문장으로 마무리해."
    )
    return {"response": reply.content}


def add_to_cart(state: ChatState, config) -> dict:
    products = state.get("products") or []
    if not products:
        return {"added_product_id": None}

    decision = interrupt(
        {
            "type": "confirm_add_to_cart",
            "candidates": [{"id": p["id"], "name": p["name"]} for p in products],
        }
    )

    if not decision or not decision.get("confirm") or not decision.get("product_id"):
        return {"added_product_id": None}

    configurable = config["configurable"]
    CartRepository(configurable["db"]).add_item(
        user_id=configurable["user_id"], product_id=decision["product_id"], quantity=1
    )
    return {"added_product_id": decision["product_id"]}
