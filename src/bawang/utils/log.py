import logging


_NOISY_LOGGERS = (
    "httpx",
    "httpcore",
    "urllib3",
    "cloudscraper",
)


def configure_logging(level: int = logging.WARNING) -> None:
    logging.basicConfig(
        level=level,
        format="%(levelname)s %(name)s: %(message)s",
    )
    for name in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
