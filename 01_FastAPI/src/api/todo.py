from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from database.connection import get_db
from database.orm import ToDo, User
from database.repository import ToDoRepository, UserRepository, get_todo_by_todo_id, get_todos
from schema.request import CreateToDoRequest
from schema.response import ToDoListSchema, ToDoSchema
from security import get_access_token
from service.user import UserService

router = APIRouter(prefix="/todos", tags=["todos"])


#############################
# GET: 조회
#############################
@router.get("", status_code=200)
def get_todos_handler(
    access_token: str = Depends(get_access_token),
    order: str | None = None,
    user_service: UserService = Depends(),
    user_repo: UserRepository = Depends(),
    todo_repo: ToDoRepository = Depends() # Session = Depends(get_db)
) -> ToDoListSchema:
    
    # print(access_token)

    username: str = user_service.decode_jwt(access_token=access_token)

    user: User | None = user_repo.get_user_by_username(username=username)
    if not  user:
        raise HTTPException(status_code=404, detail="User Not Found")
    
    todos: List[ToDo] = user.todos # get_todos(session=todo_repo)

    if order and order == "DESC":
        return ToDoListSchema(
            todos=[ToDoSchema.model_validate(todo) for todo in todos[::-1]]
        )

    return ToDoListSchema(
        todos=[ToDoSchema.model_validate(todo) for todo in todos]
    )


@router.get("/{todo_id}", status_code=200)
def get_todo_handler(
    todo_id: int,
    session: Session = Depends(get_db)
):
    todo: ToDo | None = get_todo_by_todo_id(session=session, todo_id=todo_id)

    if todo:
        return todo
    raise HTTPException(status_code=404, detail="ToDo Not Found")


#############################
# POST: 생성
#############################
@router.post("", status_code=201)
def create_todo_handler(
    request: CreateToDoRequest,
    todo_repo: ToDoRepository = Depends()
):
    todo: ToDo = ToDo.create(request=request)
    todo: ToDo = todo_repo.create_todo(todo=todo)
    return ToDoSchema.model_validate(todo)


#############################
# PATCH: 수정
#############################
@router.patch("/{todo_id}", status_code=200)
def update_todo_handler(
    todo_id: int,
    is_done: bool = Body(..., embed=True),
    session: Session = Depends(get_db),
    todo_repo: ToDoRepository = Depends()
):
    todo: ToDo | None = get_todo_by_todo_id(session=session, todo_id=todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="ToDo Not Found")

    todo.is_done = is_done
    todo: ToDo = todo_repo.update_todo(todo=todo)
    return ToDoSchema.model_validate(todo)


#############################
# DELETE: 삭제
#############################
@router.delete("/{todo_id}", status_code=204)
def delete_todo_handler(
    todo_id: int,
    session: Session = Depends(get_db),
    todo_repo: ToDoRepository = Depends()
):
    todo: ToDo | None = get_todo_by_todo_id(session=session, todo_id=todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="ToDo Not Found")

    todo_repo.delete_todo(todo_id=todo_id)
