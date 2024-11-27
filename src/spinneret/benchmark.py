"""The benchmark module"""

import time
import tracemalloc
from contextlib import contextmanager
from daiquiri import getLogger


logger = getLogger(__name__)


@contextmanager
def monitor(name: str) -> None:
    """
    Context manager to monitor the duration and memory usage of a function
    using the `daiquiri` package logger.

    :param name: The name of the function being monitored.
    :return: None
    """
    start_time = time.time()
    tracemalloc.start()
    logger.info(f"Starting function '{name}'")
    try:
        yield  # The code inside the `with` block runs here
    except Exception as e:
        logger.error(f"Function '{name}' raised an exception: {e}")
        raise
    finally:
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        duration = time.time() - start_time
        logger.info(f"Function '{name}' completed in {duration:.4f} seconds")
        logger.info(
            f"Memory usage: Current={current / 1024:.2f} KB; Peak={peak / 1024:.2f} KB"
        )
