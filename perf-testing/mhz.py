import time
from array import array


def benchmark_ops(n):
    total = 0
    for i in range(n):
        total = total + 1
    return total


iterations = 1000000
t0 = time.monotonic()
result = benchmark_ops(iterations)
t1 = time.monotonic()

elapsed = t1 - t0
ops_per_sec = iterations / elapsed

print(f"Time: {elapsed:.3f}s")
print(f"Operations/sec: {ops_per_sec:.0f}")
print(
    f"Effective MHz (assuming ~6 bytecodes/op): {ops_per_sec * 6 / 1_000_000:.2f} MHz"
)
