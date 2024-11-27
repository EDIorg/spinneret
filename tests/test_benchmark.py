"""Test benchmark code"""

import logging
import daiquiri
from spinneret.benchmark import monitor


def test_monitor(tmp_path):
    """Test the monitor context manager"""

    def example_function():  # to call with monitor
        return 1 + 1

    log_file = tmp_path / "test.log"  # set up daiquiri logger
    daiquiri.setup(
        level=logging.INFO,
        outputs=(
            daiquiri.output.File(log_file),
            "stdout",
        ),
    )

    with monitor("example_function"):  # test with monitor context manager
        example_function()

    with open(log_file, "r", encoding="utf-8") as file:
        log = file.read()
    assert "Starting function 'example_function'" in log
    assert "Function 'example_function' completed in" in log
    assert "Memory usage: Current=" in log
