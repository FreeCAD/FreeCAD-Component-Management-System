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

from typing import Literal, Optional

import jwt
from flask import request
from flask_sqlalchemy.query import Query
from werkzeug.exceptions import HTTPException

from src.models.users.models import User

from src.models.users.models import User

from ...authentication.utils import decode_auth_token
from ...log import logger
from ..licenses import SPDX
from ..licenses.schemas import spdx_schema
from ..attributes import Attribute
from ..files import File, FileType
from ..files.operations import upload_to_github
from ..metadatas import Metadata
from ..metadatas import _create as create_metadata
from ..metadatas import add_attributes, add_tags, metadata_schema, metadatas_schema
from ..tags import Tag
from ..utils import paginated_schema
from ..utils.pagination import MAX_PER_PAGE
from .schema import ComponentSchema, component_schema


def read(
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    search_str: Optional[str] = None,
    sort_by: Optional[str] = "name",
    sort_ord: Literal["desc"] | Literal["asc"] = "asc",
    file_types: list = [t.name for t in FileType],
    tags: Optional[list] = None,
    columns: Optional[list] = None,
):
    """
    Reads components from the database based on the specified parameters.

    Parameters
    ----------
    page : Optional[int], optional
                    The page number for pagination. Defaults to None.
    page_size : Optional[int], optional
                    The number of components per page. Defaults to None.
    search_str : Optional[str], optional
                    The search key to filter components by name. Defaults to None.
    sort_by : Optional[str], optional
                    The field to sort components by. Defaults to "name".
    sort_ord : Literal["desc"] | Literal["asc"], optional
                    The sort order for the components. Defaults to "asc".
    file_types : list, optional
                    The list of file types to filter components by. Defaults to [t.name for t in FileType].
    tags : Optional[list], optional
                    The list of tags to filter components by. Defaults to None.
    columns : Optional[list], optional
                    The list of columns to include in the query result. Defaults to None.

    Returns
    -------
    tuple
                    A tuple containing the components response and the HTTP status code.

    Notes
    -----
    This function reads components from the database based on the specified parameters. It applies filters, sorting, and pagination to the query.
    """

    # ! if the given page number is greater that available, there is an unhandled error(404)

    query: Query = Metadata.query

    if tags:
        query = query.filter(Metadata.tags.any(Tag.label.in_(tags)))

    query = query.filter(Metadata.files.any(File.type.in_(file_types)))

    if search_str:
        query = query.filter(
            Metadata.name.in_(Metadata.elasticsearch(search_str.lower()))
        )
        if ":" in search_str:
            matching_attrs = Attribute.elasticsearch(search_str.lower())
            logger.debug(f"{matching_attrs}")
            query = query.filter(Metadata.id.in_(matching_attrs))

    if columns:
        query = query.with_entities(*[eval(f"Metadata.{col}") for col in columns])

    order_exp = eval(f"Metadata.{sort_by}.{sort_ord}()")
    query = query.order_by(order_exp)
    paginated_query = query.paginate(
        page=page, per_page=page_size, max_per_page=MAX_PER_PAGE
    )

    components_resp = paginated_schema(ComponentSchema).dump(paginated_query)
    metadata_resp = metadatas_schema.dump(paginated_query)

    for component, metadata in zip(components_resp.get("items"), metadata_resp):
        component["metadata"] = metadata
        component["id"] = metadata["id"]
        if not component.get("license"):
            # query for license from metadata[license_id] and set it to component["license"]
            license = SPDX.query.filter(SPDX.id == metadata["license_id"]).one_or_none()
            component["license"] = spdx_schema.dump(license)

    return components_resp, 200


def create(component_data: dict):
    """
    Creates a component based on the provided component data.

    Parameters
    ----------
    component_data : dict
            The data for the component, including author, description, license_id, maintainer, name, version, and tags.

    Returns
    -------
    tuple
            A tuple containing the component response and the HTTP status code.

    Notes
    -----
    This function creates a component by creating metadata, adding tags, and uploading to GitHub. It returns the component response along with the HTTP status code.
    """

    token = request.headers.get("JWT")
    logger.debug(f"{token=}")
    if not token:
        return "token not found", 498

    try:
        user_id = decode_auth_token(token)
    except jwt.ExpiredSignatureError:
        logger.error("Token expired. Please log in again.")
        return "Token expired. Please log in again.", 498
    except jwt.InvalidTokenError:
        logger.error("Invalid token. Please log in again.")
        return "Invalid token. Please log in again.", 498

    user: User = User.query.filter(User.id == user_id).one_or_none()

    logger.debug(f"Creating component with data: {component_data}")

    metadata_data: dict = {
        "author": component_data.get("author", ""),
        "description": component_data.get("description", ""),
        "license_id": component_data.get("license_id", ""),
        "user_id": str(user.id),
        "maintainer": component_data.get("maintainer", ""),
        "name": component_data.get("name", ""),
        "rating": 0,
        "version": component_data.get("version", ""),
    }

    try:
        metadata: Metadata = create_metadata(metadata_data)
    except ValueError as err:
        logger.error(f"Error creating component: {err}")
        return str(err), 406

    user.metadatas.append(metadata)
    user.commit()
    add_tags(metadata.id, component_data.get("tags"))
    add_attributes(metadata.id, component_data.get("attributes"))
    component_data["metadata_id"] = str(metadata.id)
    upload_to_github(component_data)

    compo_response: dict = component_schema.dump(metadata)
    compo_response["metadata"] = metadata_schema.dump(metadata)

    return compo_response, 201
