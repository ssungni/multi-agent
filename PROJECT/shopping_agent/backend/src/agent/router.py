from uuid import uuid4

from fastapi import APIRouter, Depends
from langgraph.types import Command
from sqlalchemy.orm import Session

from src.agent.graph import compiled_graph
from src.agent.schemas import ChatRequest, ChatResponse, ConfirmRequest
from src.auth.dependencies import get_current_user
from src.auth.models import User
from src.core.database import get_db

router = APIRouter(prefix="/agent", tags=["agent"])


def _respond(thread_id: str, result: dict, config: dict) -> ChatResponse:
    state = compiled_graph.get_state(config)
    return ChatResponse(
        thread_id=thread_id,
        message=result.get("response", ""),
        products=result.get("products", []),
        awaiting_confirmation=bool(state.next),
        added_product_id=result.get("added_product_id"),
    )


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    thread_id = req.thread_id or f"user-{user.id}-{uuid4()}"
    config = {"configurable": {"thread_id": thread_id, "db": db, "user_id": user.id}}
    result = compiled_graph.invoke({"query": req.message}, config=config)
    return _respond(thread_id, result, config)


@router.post("/chat/confirm", response_model=ChatResponse)
def confirm(req: ConfirmRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    config = {"configurable": {"thread_id": req.thread_id, "db": db, "user_id": user.id}}
    result = compiled_graph.invoke(
        Command(resume={"confirm": req.confirm, "product_id": req.product_id}), config=config
    )
    return _respond(req.thread_id, result, config)
