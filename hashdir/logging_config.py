import logging


def setup_logger() -> logging.Logger:
    """Perform setup of logging configuration."""
    logger = logging.getLogger()
    logger_handler = logging.StreamHandler()
    logger.addHandler(logger_handler)
    logger_handler.setFormatter(logging.Formatter("\n%(levelname)s: %(message)s"))
    logger.setLevel(logging.INFO)
    return logger
