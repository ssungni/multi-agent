'''
FastAPI의 동기/비동기 함수 처리
'''

from fastapi import FastAPI

app = FastAPI(title="FastAPI Async")

@app.get("/sync")
def sync_handler():
    return "Hello, Sync"

@app.get("/async")
async def sync_handler():
    return "Hello, Sync"
