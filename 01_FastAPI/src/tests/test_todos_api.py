from fastapi.testclient import TestClient
from database.orm import ToDo, User
from database.repository import UserRepository
from service.user import UserService
# from main import app

# client = TestClient(app = app) 
# ..\fastapi\src\tests\conftest.py에 구현해서 지워도 됨

def test_get_todos(client, mocker):
    access_token: str = UserService().create_jwt(username="test")
    headers = {"Authorization": f"Bearer {access_token}"}

    user = User(id=1, username="test", password="hashed")
    user.todos = [
        ToDo(id=1, contents="FastAPI Section 0", is_done=True),
        ToDo(id=2, contents="FastAPI Section 1", is_done=False),
    ]

    mocker.patch.object(
        UserRepository, "get_user_by_username", return_value=user
    )

    # order = ASC
    mocker.patch("main.get_todos", return_value = [
        ToDo(id = 1, contents="Laudry", is_done=True), 
        ToDo(id = 2, contents="Homework", is_done=False), 
    ])
    response = client.get("/todos")
    assert response.status_code == 200
    assert response.json() == {
        "todos": [
            {"id": 1, "contents": "Laudry", "is_done": True}, 
            {"id": 2, "contents": "Homework", "is_done": False}, 
           # {"id": 3, "contents": "Essay", "is_done": False}, 
        ]}
    
    
    # order = DESC
    response = client.get("/todos?order=DESC")
    assert response.status_code == 200
    assert response.json() == {
        "todos": [
            #{"id": 3, "contents": "Essay", "is_done": False}, 
            {"id": 2, "contents": "Homework", "is_done": False}, 
            {"id": 1, "contents": "Laudry", "is_done": True}, 
        ]}
    

def test_get_todo(client, mocker):
    mocker.patch(
        "main.get_todo_by_todo_id", 
        return_value = ToDo(id=1, contents = "todo", is_done = True)
    
    )
    response = client.get("/todos/1")
    assert response.status_code == 200
    assert response.json() == {"id": 1, "contents": "todo", "is_done": True}
