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

from flask_sqlalchemy.session import Session
from marshmallow import fields
from sqlalchemy.orm.scoping import scoped_session

from ...database import db, ma
from .models import Metadata


class MetadataSchema(ma.SQLAlchemyAutoSchema):
    """
    A Marshmallow schema for serializing and deserializing Metadata objects.

    Attributes:
        license_id (str): The license ID field.

    Meta:
        model (Metadata): The Metadata model class.
        load_instance (bool): Whether to load instances of the model.
        sqla_session (scoped_session[Session]): The SQLAlchemy session.

    """

    license_id = fields.String()
    user_id = fields.String()

    class Meta:
        model = Metadata
        load_instance = True
        sqla_session: scoped_session[Session] = db.session


metadata_schema = MetadataSchema()
metadatas_schema = MetadataSchema(many=True)

Metadata.set_schemas(metadata_schema, metadatas_schema)
