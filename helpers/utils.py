import time


def chunkify(li, size):
    for i in range(0, len(li), size):
        yield li[i:i+size]


def time_since(start_time: float):
    return time.time() - start_time
