import logging
from logging.config import dictConfig

from .config import Config

logger: logging.Logger = logging.getLogger(__name__)

# Stream handler
__stream_handler = logging.StreamHandler(Config.LOG.STREAM.STREAM)
__stream_handler.setLevel(Config.LOG.STREAM.LEVEL)
__stream_formatter = logging.Formatter(Config.LOG.STREAM.FORMAT)
__stream_handler.setFormatter(__stream_formatter)
logger.addHandler(__stream_handler)


# File handler
__file_handler = logging.FileHandler(
	filename = Config.LOG.FILE.PATH,
    mode = "a",
    encoding = None,
    delay = False,
    errors = None,
)
__file_handler.setLevel(Config.LOG.FILE.LEVEL)
__file_formatter = logging.Formatter(Config.LOG.FILE.FORMAT)
__file_handler.setFormatter(__file_formatter)
logger.addHandler(__file_handler)

def setup_logger():
	dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "default",
            }
        },
        "root": {"level": "DEBUG", "handlers": ["console"]},
    }
)
