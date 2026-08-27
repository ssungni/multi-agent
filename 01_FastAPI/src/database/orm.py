# sqlalchemy는 sql을 작성하지 않고도 Python 클래스로 표현하겠다!

from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

from schema.request import CreateToDoRequest
# orm
# 데이터베이스 테이블과 클래스를 연동시키는 것

Base = declarative_base() # 아 이건 일반 클래스가 아니라 db 테이블이네.

class ToDo(Base):
    __tablename__ = "todo"

    id = Column(Integer, primary_key=True, index = True)
    contents = Column(String(256), nullable=False)
    is_done = Column(Boolean, nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"))

    def __repr__(self): # 개발자에게 보여주기 위한 출력문
        return f"ToDo(id={self.id}, contents={self.contents}, is_done={self.is_done})"

    @classmethod
    def create(cls, request: CreateToDoRequest) -> "ToDo":
        return cls(
            contents=request.contents,
            is_done=request.is_done
        )

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index = True)
    username = Column(String(256), nullable=False)
    password = Column(String(256), nullable=False)
    todos = relationship("ToDo", lazy = "joined")
    
    @classmethod
    def create(cls, username: str, hashed_password: str) -> "User":
        return cls(
            username=username,
            password=hashed_password
        )