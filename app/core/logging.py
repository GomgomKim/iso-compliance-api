import sys
from loguru import logger
from app.core.config import settings


def setup_logging():
    """Configure application logging with loguru."""

    # Remove default handler
    logger.remove()

    # Console handler
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.LOG_LEVEL,
    )

    # File handler (optional, for production)
    if settings.APP_ENV == "production":
        logger.add(
            "logs/api.log",
            rotation="500 MB",
            retention="10 days",
            compression="zip",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="INFO",
        )

    logger.info(f"Logging configured for {settings.APP_ENV} environment")


def get_logger(name: str):
    """Get a logger instance with the given name."""
    return logger.bind(name=name)
