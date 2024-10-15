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

import os

import certifi
from elasticsearch import Elasticsearch
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

ma = Marshmallow()

es = Elasticsearch(
    "https://elasticsearch.localhost:9200/",
    basic_auth=(
        os.environ.get("ELASTICSEARCH_USERNAME", ""),
        os.environ.get("ELASTICSEARCH_PASSWORD", ""),
    ),
    # ca_certs=certifi.where(),
    verify_certs=False,
)
