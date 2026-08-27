'''
동기/비동기 차이
'''

import asyncio
import time

#동기
def process_order(num):
    print(f"{num}번 주문")
    print(f"{num}번 요리 시작")
    time.sleep(3)
    print(f"{num}번 음식 완성")

process_order(1) # 3초
print("==========")
process_order(2) # 6초
print("==========")
process_order(3)

# 비동기
async def process_order(num):
    print("==========")
    print(f"{num}번 주문")
    print(f"{num}번 요리 시작")
    await asyncio.sleep(3)
    print("==========")
    print(f"{num}번 음식 완성")

async def main():
    await asyncio.gather(
        process_order(1), process_order(2), process_order(3) 
    )

asyncio.run(main())