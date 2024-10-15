import logging

import urllib3
from elasticsearch import logger as es_logger

from ..config import Config
from .handlers import BaseRotatingFileHandler, BaseStreamHandler

logging.basicConfig(
    level=Config.LOG_LEVEL,
    handlers=[],  # *if here handlers are added, then there are double log entries in different formats
)
# TODO : the log levels are hard coded. use the config logging level value

logger: logging.Logger = logging.getLogger("root")
logger.addHandler(BaseStreamHandler())
logger.addHandler(BaseRotatingFileHandler())

es_logger.addHandler(BaseStreamHandler())
es_logger.addHandler(BaseRotatingFileHandler())

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
