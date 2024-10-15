# SPDX-License-Identifier: MIT
# --------------------------------------------------------------
# |																|
# |             Copyright 2023 - 2023, Amulya Paritosh			|
# |																|
# |  This file is part of Component Library Plugin for FreeCAD.	|
# |																|
# --------------------------------------------------------------

from os import path

import connexion
from connexion import FlaskApp
from flask import Flask

from ..config import Config, basedir
from ..database.utils import setup_db
from ..log.handlers import FlaskHandler
from .routes import create_routes


def create_app(config_class=Config) -> Flask:
    """
    Creates and configures the Flask application.

    Args:
                    config_class (Config): The configuration class to use for the application.

    Returns:
                    Flask: The configured Flask application.

    Example:
                    ```python
                    app = create_app()
                    ```
    """

    connex_app: FlaskApp = connexion.FlaskApp(__name__, specification_dir=basedir)
    connex_app.add_api(path.join(basedir, "app/swagger.yml"))

    app: Flask = connex_app.app
    app.config.from_object(config_class)

    setup_db(app)
    create_routes(app)

    app.logger.name = "api"
    app.logger.handlers.clear()
    app.logger.addHandler(FlaskHandler.StreamHandler())
    app.logger.addHandler(FlaskHandler.RotatingFileHandler())
    app.logger.setLevel(Config.LOG_LEVEL)

    return app
