import logging
import logging.handlers
import sys

from flask import has_request_context, request

from ..config import Config


class RequestFormatter(logging.Formatter):
    def format(self, record) -> str:
        if has_request_context():
            record.url = request.url
            record.remote_addr = request.remote_addr
        else:
            record.url = None
            record.remote_addr = None

        return super().format(record)


class BaseStreamHandler(logging.StreamHandler):
    def __init__(self) -> None:
        super().__init__()
        self.formatter = logging.Formatter("[%(levelname)s] - %(name)s : %(message)s")
        self.level = Config.LOG_LEVEL
        self.stream = sys.stderr


class BaseRotatingFileHandler(logging.handlers.RotatingFileHandler):
    def __init__(self) -> None:
        super().__init__(
            filename="test/component_management_system.log",
            mode="a",
            maxBytes=1024 * 1024,
            encoding="utf-8",
        )
        self.level = Config.LOG_LEVEL
        self.formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] - %(name)s in {%(module)s}\n%(message)s"
        )


class FlaskHandler:
    class StreamHandler(BaseStreamHandler):
        ...

    class RotatingFileHandler(BaseRotatingFileHandler):
        formatter = RequestFormatter(
            "[%(asctime)s] [%(levelname)s] - %(name)s - %(url)s in {%(module)s}\n%(message)s"
        )
