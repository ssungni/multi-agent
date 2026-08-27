from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from src.agent import nodes
from src.agent.state import ChatState


def build_graph():
    graph = StateGraph(ChatState)
    graph.add_node("extract_intent", nodes.extract_intent)
    graph.add_node("search_products", nodes.search_products)
    graph.add_node("retry_search", nodes.retry_search)
    graph.add_node("rank_and_respond", nodes.rank_and_respond)
    graph.add_node("add_to_cart", nodes.add_to_cart)

    graph.set_entry_point("extract_intent")
    graph.add_edge("extract_intent", "search_products")
    graph.add_conditional_edges(
        "search_products",
        nodes.route_after_search,
        {"retry_search": "retry_search", "rank_and_respond": "rank_and_respond"},
    )
    graph.add_edge("retry_search", "rank_and_respond")
    graph.add_edge("rank_and_respond", "add_to_cart")
    graph.add_edge("add_to_cart", END)

    return graph.compile(checkpointer=MemorySaver())


# 프로세스 메모리 체크포인터라 서버 재시작 시 진행 중이던 interrupt 상태는 사라짐 (README에 명시된 known limitation)
compiled_graph = build_graph()
