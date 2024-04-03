import logging
import os
import sys


def logger_setup(module: str, level: int = logging.DEBUG, log_to_file: bool = True) -> logging.Logger:
    module_name = module.split(".")[-1]

    os.makedirs("logs", exist_ok=True)

    logger = logging.getLogger(module)

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    if log_to_file:
        handler = logging.FileHandler(f"logs/{module_name}.log")
    else:
        handler = logging.StreamHandler(sys.stdout)

    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.setLevel(level)

    return logger


class NullLogger(logging.Logger):

    class NullHandler(logging.Handler):
        def emit(self, record: logging.LogRecord):
            pass

    def __init__(self):
        super().__init__(__name__, logging.DEBUG)

        null_handler = self.NullHandler()
        null_handler.setLevel(logging.DEBUG)

        self.addHandler(null_handler)
