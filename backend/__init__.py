"""
Backend package initialization
This file makes the backend directory a proper Python package
"""

import os
import logging

formatter = logging.Formatter(
    fmt="%(asctime)s-%(levelname)s - %(message)s", datefmt="%Y-%m-%d,%H:%M:%S"
)

logger = logging.getLogger("console_logger")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

f_logger = logging.getLogger("file_logger")
f_logger.setLevel(logging.DEBUG)

f_handler = logging.FileHandler(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_log.txt"),
    mode="w"
)
f_handler.setFormatter(formatter)
f_logger.addHandler(f_handler)
