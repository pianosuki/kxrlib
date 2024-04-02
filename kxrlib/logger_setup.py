import logging
import os


def logger_setup(module: str, level: int = logging.DEBUG) -> logging.Logger:
    module_name = module.split(".")[-1]

    os.makedirs("logs", exist_ok=True)

    logger = logging.getLogger(module)

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    file_handler = logging.FileHandler(f"logs/{module_name}.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.setLevel(level)

    return logger
