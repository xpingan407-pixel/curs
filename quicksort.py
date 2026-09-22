"""快速排序（Quick Sort）示例实现。"""

from __future__ import annotations

from typing import List, TypeVar

T = TypeVar("T")


def quicksort(arr: List[T]) -> List[T]:
    """
    对列表进行原地快速排序（升序），并返回同一列表引用。

    算法思路：
    1. 选取基准值 pivot（此处取区间最后一个元素，便于实现）。
    2. 分区（partition）：将小于 pivot 的元素移到左侧，大于等于的移到右侧。
    3. 对左右两个子区间递归排序。

    时间复杂度：
    - 平均：O(n log n)。每层分区约 O(n)，递归深度期望为 O(log n)。
    - 最好：O(n log n)。每次分区较均衡（如中位数作 pivot）。
    - 最坏：O(n²)。每次 pivot 都是最小或最大（如已排序且总选端点）。

    空间复杂度：
    - 平均 O(log n)，来自递归调用栈；最坏 O(n)。
    """
    if len(arr) <= 1:
        return arr
    _quicksort_inplace(arr, 0, len(arr) - 1)
    return arr


def _quicksort_inplace(arr: List[T], low: int, high: int) -> None:
    """在 arr[low:high] 闭区间内递归排序。"""
    if low >= high:
        return

    # 分区后 pivot 的最终下标
    pivot_index = _partition(arr, low, high)

    # 左子区间不包含 pivot，右子区间从 pivot+1 开始
    _quicksort_inplace(arr, low, pivot_index - 1)
    _quicksort_inplace(arr, pivot_index + 1, high)


def _partition(arr: List[T], low: int, high: int) -> int:
    """
    Lomuto 分区：以 arr[high] 为 pivot。

    返回 pivot 在排序后应处的下标。
    """
    pivot = arr[high]
    # i 指向「小于 pivot」区域的最后一个位置
    i = low - 1

    for j in range(low, high):
        if arr[j] < pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]

    # 将 pivot 放到正确位置
    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    return i + 1


if __name__ == "__main__":
    sample = [64, 34, 25, 12, 22, 11, 90]
    print("排序前:", sample)
    quicksort(sample)
    print("排序后:", sample)
