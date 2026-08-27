'''
코루틴(coroutine) 함수 정의 및 실행 

- async def로 만든 함수는 호출해도 즉시 실행되지 않음
- 코루틴 객체만 반환되며, asyncio.run()으로 실행해야 실제 동작함
'''

import asyncio

async def hello():
    print("Hello, World!")

hello_coroutine = hello()
asyncio.run(hello_coroutine)