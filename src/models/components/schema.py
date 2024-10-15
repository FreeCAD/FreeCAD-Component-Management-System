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

from marshmallow import Schema, fields

from ..attributes import AttributesSchema
from ..files import FileSchema
from ..licenses import SPDXSchema
from ..metadatas import MetadataSchema
from ..tags import TagSchema


class ComponentSchema(Schema):
    """
    Represents the schema for a component.

    Parameters
    ----------
    Schema : class
            The base class for defining a schema.

    Attributes
    ----------
    id : str
            The ID of the component.
    metadata : MetadataSchema
            The metadata of the component.
    license : SPDXSchema
            The license of the component.
    files : List[FileSchema]
            The files associated with the component.
    tags : List[TagSchema]
            The tags associated with the component.
    """

    id = fields.String()
    metadata = fields.Nested(MetadataSchema)
    license = fields.Nested(SPDXSchema)
    files = fields.Nested(FileSchema, many=True)
    tags = fields.Nested(TagSchema, many=True)
    attributes = fields.Nested(AttributesSchema, many=True)


component_schema = ComponentSchema()
components_schema = ComponentSchema(many=True)
