"""Host execution controls; these never change simulated worker capabilities."""

import contextlib
import multiprocessing as mp
import threading
import time

_local = threading.local()


class SimulationCancelled(Exception):
    """The user requested cancellation; partial results are not successful runs."""


def check_cancelled():
    """Cooperative checkpoint for work performed in the application thread."""
    event = getattr(_local, "cancel_event", None)
    if event is not None and event.is_set():
        raise SimulationCancelled("Simulation cancelled.")


@contextlib.contextmanager
def cancellation(event):
    """Install a cancellation signal for this thread, including calibration."""
    previous = getattr(_local, "cancel_event", None)
    _local.cancel_event = event
    try:
        check_cancelled()
        yield
    finally:
        _local.cancel_event = previous


class HostPool:
    """Ordered map with bounded spawn workers, cancellation and failure propagation.

    One worker runs directly. Multi-worker pools can be reused for many PoW
    batches. Every map has a timeout so a lost worker cannot block forever.
    """

    def __init__(self, workers=1, timeout=120.0):
        if type(workers) is not int or workers < 1:
            raise ValueError("host_workers must be a positive integer")
        if timeout <= 0:
            raise ValueError("worker timeout must be positive")
        self.workers, self.timeout = workers, timeout
        self.pool = None

    def __enter__(self):
        check_cancelled()
        return self

    def map(self, function, arguments):
        arguments = list(arguments)
        check_cancelled()
        if not arguments:
            return []
        if self.workers == 1:
            results = []
            for argument in arguments:
                check_cancelled()
                results.append(function(argument))
            check_cancelled()
            return results
        if self.pool is None:
            self.pool = mp.get_context("spawn").Pool(
                min(self.workers, len(arguments))
            )
        job = self.pool.map_async(function, arguments)
        deadline = time.monotonic() + self.timeout
        while True:
            check_cancelled()
            try:
                return job.get(timeout=0.05)
            except mp.TimeoutError:
                if time.monotonic() >= deadline:
                    raise TimeoutError("Host worker timed out; run rejected.")

    def __exit__(self, exc_type, exc, traceback):
        if self.pool is not None:
            if exc_type is None:
                self.pool.close()
            else:
                self.pool.terminate()
            self.pool.join()


def host_map(function, arguments, workers=1):
    """Execute one phase without changing logical task ordering or task count."""
    with HostPool(workers) as pool:
        return pool.map(function, arguments)
