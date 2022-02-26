from Libs.globals import *


def profiler(fn: typing.Callable):
    def inner():
        start_time = time.perf_counter_ns()
        fn()
        elapsed = time.perf_counter_ns() - start_time
        print(f"Elapsed: {elapsed / 10 ** 6:.03f} on function {fn.__name__}")

    return inner()


class ProfilerContext:
    def __init__(self, name: str):
        self.name = name

    def __enter__(self):
        self._start = time.perf_counter_ns()

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = (time.perf_counter_ns() - self._start) / 10**6
        print(f"Elapsed: {elapsed:.03f}ms", end="" or f", (or {elapsed / 1000:.02f} secs.), " if elapsed > 1000 else " ")
        print(f"on \"{self.name}\"")
