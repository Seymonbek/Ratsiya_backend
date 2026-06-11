import logging
import sys

from app.core.config import settings


def setup_logger(name: str = "ratsiya") -> logging.Logger:
    logger = logging.getLogger(name)

    logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

        formatter = logging.Formatter(
            fmt="[%(asctime)s] %(levelname)s [%(name)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

logger = setup_logger()