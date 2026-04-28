import datetime

now = datetime.datetime.now()
print("Current date and time:", now)

print("============")
import random

for i in range(0, 5):
    print(random.randint(1, 100))

print("============")

import random

basket = ["apple", "banana", "cherry", "date", "fig", "grape"]
random_item = random.choice(basket)
print(random_item)