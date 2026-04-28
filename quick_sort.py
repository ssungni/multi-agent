import random

def quick_sort(arr):
    # 피벗을 뽑는다.
    if len(arr) <= 1:
        return arr
    
    pivot = random.choice(arr)
    less = []
    equal = []
    greater = []

    for item in arr:
        if item > pivot:
            greater.append(item)
        elif item < pivot:
            less.append(item)
        else:
            equal.append(item)

    # 재귀적으로 정렬
    return quick_sort(less) + equal + quick_sort(greater)

arr1 = [3, 6, 8, 10, 1, 2, 1]
arr2 = [10, 7, 8, 9, 1, 5]
arr3 = [1, 2, 3, 4, 5]

print(quick_sort(arr1))
print(quick_sort(arr2))
print(quick_sort(arr3))