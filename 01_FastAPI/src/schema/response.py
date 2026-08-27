from typing import List

from pydantic import BaseModel, ConfigDict

class ToDoSchema(BaseModel):
    id: int
    contents: str 
    is_done: bool

    # ORM 모델은 현재 SQLAlchemy 객체로,
    '''
    class ToDo(Base):
        id = Column(Integer, primary_key=True)
        contents = Column(String)
        is_done = Column(Boolean)
    
    '''
    # 속성의 값을 가지고 있음
    '''
        todo = ToDo(
            id=1,
            contents="Laundry",
            is_done=True
        )
    '''

    '''
        todo.id
        todo.contents
        todo.is_done
    '''

    ##############################################

    # 응답은 
    '''
    class ToDoSchema(BaseModel):
        id: int
        contents: str 
        is_done: bool
    '''
    '''
    {
        "id": 1,
        "contents": "Laundry",
        "is_done": true
    }
    '''

    # v1
    # class Config:
    #     orm_mode = True # orm_mode = True를 해야지 변경이 되는 것임
    model_config = ConfigDict(from_attributes=True)

class ToDoListSchema(BaseModel):
    todos: List[ToDoSchema]
    

class UserSchema(BaseModel):
    id: int
    username: str
    model_config = ConfigDict(from_attributes=True)

class JWTResponse(BaseModel):
    access_token: str