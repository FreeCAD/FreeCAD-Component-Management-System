# SPDX-License-Identifier: MIT
# --------------------------------------------------------------
# |																|
# |             Copyright 2023 - 2023, Amulya Paritosh			|
# |																|
# |  This file is part of Component Library Plugin for FreeCAD.	|
# |																|
# |               This file was created as a part of				|
# |              Google Summer Of Code Program - 2023			|
# |																|
# --------------------------------------------------------------

import logging
import os

basedir: str = os.path.abspath(os.path.dirname(__file__))
from typing import Optional


class Config:
    """
    Configuration class for the Component Management System.

    Attributes
    ----------
    SECRET_KEY : str | None
        The secret key for the Flask application. Defaults to the value of the "FLASK_SECRET_KEY" environment variable.
    DEBUG : bool
        Flag indicating whether debug mode is enabled. Defaults to True.
    TESTING : bool
        Flag indicating whether testing mode is enabled. Defaults to True.
    SQLALCHEMY_DATABASE_URI : str
        The URI for the SQLAlchemy database connection. Defaults to a SQLite database located at "{basedir}/app.db".
    SQLALCHEMY_TRACK_MODIFICATIONS : bool
        Flag indicating whether SQLAlchemy should track modifications. Defaults to False.

    Notes
    -----
    This class represents the configuration settings for the Component Management System.
    It provides default values for various attributes used in the application.
    """

    SQLALCHEMY_DATABASE_URI: str = os.environ.get("SQLALCHEMY_DATABASE_URI", "")
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = (
        os.environ.get("SQLALCHEMY_TRACK_MODIFICATIONS", "0") == "1"
    )

    LOG_LEVEL = logging.DEBUG

    GITHUB_OAUTH_CLIENT_ID: Optional[str] = os.environ.get("GITHUB_OAUTH_CLIENT_ID")
    GITHUB_OAUTH_CLIENT_SECRET: Optional[str] = os.environ.get(
        "GITHUB_OAUTH_CLIENT_SECRET"
    )

    FLASK_SECRET: str = os.environ.get("FLASK_SECRET_KEY")
