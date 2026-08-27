# FastAPI

FastAPI로 만든 ToDo / User API 프로젝트입니다.

## 실행

`src/test.py`에 FastAPI 기본 사용법(GET, POST, PUT, DELETE)이 간단하게 정리되어 있습니다.

```
uvicorn test:app --reload
```

실제 애플리케이션(`src/main.py`)은 아래와 같이 실행합니다.

```
cd src
uvicorn main:app --reload
```

## 설치

```
pip install fastapi # 프레임워크

pip install uvicorn # 서버 실행

pip install sqlalchemy

pip install pymysql # python과 mysql을 연동할 때 필요

pip install redis # python과 redis를 연동할 때 필요

pip install cryptography # 인증이나 암호

pip install bcrypt # 비밀번호 해싱

pip install python-jose # JWT 생성 및 검증

pip install pytest # 테스트

pip install httpx # TestClient가 내부적으로 필요
```

## Docker

### MySQL

```
# 컨테이너 실행
docker run -p 3306:3306 -e MYSQL_ROOT_PASSWORD=todos -e MYSQL_DATABASE=todos -d -v todos:/db --name todos mysql:8.0

# 컨테이너 상태 확인
docker ps
docker logs todos
docker volume ls
```

MySQL 접속

```
docker exec -it todos bash
mysql -u root -p
```

### Redis

```
# 컨테이너 실행
docker run -p 6379:6379 --name redis -d --rm redis

# 컨테이너 상태 확인
docker ps
docker logs redis
```

### 컨테이너 종료

```
docker ps            # 종료할 컨테이너 이름/ID 확인
docker stop redis
docker stop mysql
```
