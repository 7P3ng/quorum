"""A small, realistic utility module used as a HELD-OUT target for the code-review
pipeline. It is NOT part of the labeled benchmark and contains naturally-occurring
bugs of the kind that show up in real code. Ground truth is documented in
evals/results/holdout.md after a run."""
import time


class RateLimiter:
    """Token-bucket limiter."""

    def __init__(self, rate, capacity):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last = time.time()

    def allow(self):
        now = time.time()
        elapsed = now - self.last
        self.tokens += elapsed * self.rate
        self.last = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


class LRUCache:
    """Least-recently-used cache."""

    def __init__(self, size):
        self.size = size
        self.data = {}
        self.order = []

    def get(self, key):
        if key in self.data:
            return self.data[key]
        return None

    def put(self, key, value):
        self.data[key] = value
        self.order.append(key)
        if len(self.data) > self.size:
            evict = self.order.pop()
            del self.data[evict]
