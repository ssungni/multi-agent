from fastapi import FastAPI, HTTPException

app = FastAPI()

# get, post, put, delete

# GET : 서버에 저장된 데이터를 요청할 때 사용
@app.get("/")
async def root():
    return "Hello World"

@app.get("/test")
async def test():
    return {"message": "Hello, FastAPI!"}

# POST: 서버에 새로운 데이터를 생성할 때 사용
messages = {}

@app.post("/messages")
async def post_message(message: str):
    return {"message": message}

# PUT: 기존 데이터를 수정할 때
@app.put("/messages/{message_id}")
async def put_message(message_id: int, new_message: str):
    messages[message_id] = new_message
    return {"message": f"Message {message_id} updated to '{new_message}'"}

# DELETE: 서버에 저장된 데이터를 삭제할 때 사용
@app.delete("/messages/{message_id}")
async def delete_message(message_id: int):
    if message_id not in messages:
        return HTTPException(status_code=400, detail=f"Message not exist")
    del messages[message_id]
    return {"message": f"Message {message_id} deleted"}