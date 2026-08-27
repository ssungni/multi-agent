from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "mysql+pymysql://root:todos@127.0.0.1:3306/todos"

engine = create_engine(DATABASE_URL)
# echo=True
# 코드 청크의 소스 코드와 그 결과(그래프, 텍스트 등)가 모두 렌더링 결과물에 표시됩니다.

# echo=FALSE
# 소스 코드는 숨겨지고, 코드가 실행되어 생성된 최종 결과(예: 그래프나 표)만 문서에 나타납니다.

SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()
        