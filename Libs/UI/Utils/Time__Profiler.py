from Libs.globals import *


def profiler(fn: typing.Callable):
    def inner():
        start_time = time.perf_counter_ns()
        fn()
        elapsed = time.perf_counter_ns() - start_time
        print(f"Elapsed: {elapsed / 10 ** 6:.03f} on function {fn.__name__}")

    return inner()


class ProfilerContext:
    def __init__(self, name: str, print_=True):
        self.name = name
        self.print_ = print_

    def __enter__(self):
        self._start = time.perf_counter_ns()

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = (time.perf_counter_ns() - self._start) / 10 ** 6  # in ms
        if elapsed >= (60 * 1000):
            disp_str = f"{self.name} took {elapsed / (60 * 1000):.03f} minutes"
        elif elapsed >= 1000:
            disp_str = f"{self.name} took {elapsed / 1000:.03f} seconds"
        else:
            disp_str = f"{self.name} took {elapsed:.03f} ms"
        if self.print_:
            print(disp_str)
        return round(elapsed / 1000, 3)

    def start(self):
        self.__enter__()
        return self

    def stop(self):
        time_secs = self.__exit__(None, None, None)
        return time_secs
