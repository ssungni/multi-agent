'''
await로 비동기 대기(sleep)

- 다른 작업을 블로킹하지 않고 지정 시간만큼 대기 후 재개됨을 보여줌
'''
import asyncio

async def async_sleep():
    print("Start sleeping")
    await asyncio.sleep(1)
    print("Wake up")

asyncio.run(async_sleep())