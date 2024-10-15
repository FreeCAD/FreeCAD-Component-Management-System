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

from typing import Literal

from flask import Response, abort, make_response

from ...log import logger
from ..attributes import Attribute, attribute_schema, attributes_schema
from ..files import File, files_schema
from ..tags import Tag, tags_schema
from ..utils import PsudoPagination, paginated_schema, search_query
from ..utils.pagination import MAX_PER_PAGE
from .models import Metadata
from .schemas import metadata_schema, metadatas_schema


def read_all():
    """
    Reads all metadata.

    This function queries all metadata from the database and performs pseudo-pagination on the result.
    The paginated result is then serialized using the `metadatas_schema` schema.

    Returns:
            dict: The serialized paginated metadata.

    Example:
            ```python
            result = read_all()
            print(result)
            ```
    """

    query: list[Metadata] = Metadata.query.all()
    psudo_paged_query = PsudoPagination(0, None, query, len(query))
    return paginated_schema(metadatas_schema).dump(psudo_paged_query)


def read_page(page=None, page_size=None):
    """
    Reads a page of metadata.

    If `page` and `page_size` are not provided, it calls the `read_all` function to retrieve all metadata.
    Otherwise, it queries the specified page of metadata using pagination and serializes the result using the `metadatas_schema` schema.

    Args:
            page (int): The page number to retrieve.
            page_size (int): The number of items per page.

    Returns:
            dict: The serialized paginated metadata.

    Example:
            ```python
            result = read_page(page=1, page_size=10)
            print(result)
            ```
    """

    if not all((page, page_size)):
        return read_all()

    query = Metadata.query.paginate(
        page=page, per_page=page_size, max_per_page=MAX_PER_PAGE
    )
    return paginated_schema(metadatas_schema).dump(query)


def read_one(pk) -> tuple[dict[str, str], Literal[200]]:
    """
    Reads a single metadata entry.

    This function queries the metadata with the specified primary key (`pk`).
    If the metadata is found, it is serialized using the `metadata_schema` schema and returned with a status code of 200.
    If the metadata is not found, a 404 error is raised.

    Args:
            pk: The primary key of the metadata entry to retrieve.

    Returns:
            tuple: A tuple containing the serialized metadata and the status code.

    Raises:
            HTTPException: Raised when the metadata with the specified primary key is not found.

    Example:
            ```python
            result = read_one(1)
            print(result)
            ```
    """

    metadata: Metadata | None = Metadata.query.filter(Metadata.id == pk).one_or_none()

    if metadata is None:
        abort(404, f"Metadata with id {pk} not found!")

    return metadata_schema.dump(metadata), 200


def _create(metadata: dict) -> Metadata:
    """
    Creates a new metadata entry.

    Args:
            metadata (dict): The metadata to create.

    Returns:
            Metadata: The created metadata entry.

    Raises:
            HTTPException: Raised when the metadata with the same name already exists.

    Example:
            ```python
            metadata = {
                    "name": "example",
                    "description": "This is an example metadata entry."
            }
            result = _create(metadata)
            print(result)
            ```
    """

    existing_metadata = Metadata.query.filter(
        Metadata.name == metadata.get("name")
    ).one_or_none()

    if existing_metadata is not None:
        raise ValueError(f"Metadata with name {metadata.get('name')} already exists!")

    logger.info(metadata)

    new_metadata: Metadata = metadata_schema.load(metadata)
    new_metadata.create()
    return new_metadata


def create(metadata) -> tuple[dict[str, str], Literal[201]]:
    """
    Creates a new metadata entry.

    Args:
            metadata (dict): The metadata to create.

    Returns:
            tuple: A tuple containing the serialized metadata and the status code.

    Example:
            ```python
            metadata = {
                    "name": "example",
                    "description": "This is an example metadata entry."
            }
            result = create(metadata)
            print(result)
            ```
    """

    return metadata_schema.dump(_create(metadata)), 201


def delete(pk) -> Response:
    """
    Deletes a metadata entry.

    Args:
            pk: The primary key of the metadata entry to delete.

    Returns:
            Response: The response indicating the success of the deletion.

    Raises:
            HTTPException: Raised when the metadata with the specified primary key is not found.

    Example:
            ```python
            result = delete(pk=1)
            print(result)
            ```
    """

    existing_metadata: Metadata | None = Metadata.query.filter(
        Metadata.id == pk
    ).one_or_none()

    if existing_metadata is None:
        abort(404, f"Metadata with id {pk} not found")

    existing_metadata.delete()
    return make_response(f"metadata:{pk} successfully deleted", 200)


def read_tags(pk) -> list[dict[str, str]]:
    """
    Retrieves the tags of a metadata entry.

    Args:
            pk: The primary key of the metadata entry.

    Returns:
            list: A list of dictionaries representing the tags of the metadata entry.

    Raises:
            HTTPException: Raised when the metadata with the specified primary key is not found.

    Example:
            ```python
            result = read_tags(pk=1)
            print(result)
            ```
    """

    existing_metadata: Metadata | None = Metadata.query.filter(
        Metadata.id == pk
    ).one_or_none()

    if existing_metadata is None:
        abort(404, f"Metadata with id {pk} not found")

    return tags_schema.dump(existing_metadata.tags)


def add_tags(pk, tags) -> Response:
    """
    Retrieves the tags of a metadata entry.

    Args:
            pk: The primary key of the metadata entry.

    Returns:
            list: A list of dictionaries representing the tags of the metadata entry.

    Raises:
            HTTPException: Raised when the metadata with the specified primary key is not found.

    Example:
            ```python
            result = read_tags(pk=1)
            print(result)
            ```
    """

    existing_metadata: Metadata | None = Metadata.query.filter(
        Metadata.id == pk
    ).one_or_none()

    if existing_metadata is None:
        abort(404, f"Metadata with id {pk} not found")

    for tag in tags:
        existing_tag: Tag | None = Tag.query.filter(Tag.label == tag).one_or_none()

        if existing_tag is None:
            abort(404, f"tag {tag} does not exist!")

        existing_metadata.add_tag(existing_tag)

    return make_response("tags added successfully", 200)


def add_files(pk, file_ids: list) -> Response:
    """
    Adds files to a metadata entry.

    Args:
            pk: The primary key of the metadata entry.
            file_ids (list): A list of file IDs to add.

    Returns:
            Response: The response indicating the success of the operation.

    Raises:
            HTTPException: Raised when the metadata with the specified primary key or any of the file IDs are not found.

    Example:
            ```python
            result = add_files(pk=1, file_ids=[1, 2, 3])
            print(result)
            ```
    """

    existing_metadata: Metadata | None = Metadata.query.filter(
        Metadata.id == pk
    ).one_or_none()

    if existing_metadata is None:
        abort(404, f"Metadata with id {pk} not found")

    for id in file_ids:
        existing_file: File | None = File.query.filter(File.id == id).one_or_none()

        if existing_file is None:
            abort(404, f"file with id {id} does not exist!")

        existing_metadata.add_file(existing_file)

    return make_response("file added successfully", 200)


def read_files(pk) -> list[dict[str, str]]:
    """
    Retrieves the files of a metadata entry.

    Args:
            pk: The primary key of the metadata entry.

    Returns:
            list: A list of dictionaries representing the files of the metadata entry.

    Raises:
            HTTPException: Raised when the metadata with the specified primary key is not found.

    Example:
            ```python
            result = read_files(pk=1)
            print(result)
            ```
    """

    existing_metadata: Metadata | None = Metadata.query.filter(
        Metadata.id == pk
    ).one_or_none()

    if existing_metadata is None:
        abort(404, f"Metadata with id {pk} not found")

    return files_schema.dump(existing_metadata.files)


def search(search_key):
    """
    Searches for metadata entries based on a search key.

    Args:
            search_key: The search key to match against the metadata name.

    Returns:
            list: A list of dictionaries representing the matched metadata entries.

    Example:
            ```python
            result = search(search_key="example")
            print(result)
            ```
    """

    metadatas = search_query(Metadata, Metadata.name, search_key)
    return metadatas_schema.dump(metadatas)


def read_attributes(pk):
    existing_metadata: Metadata = Metadata.query.filter(Metadata.id == pk).one_or_none()

    if existing_metadata is None:
        abort(404, f"Metadata with id {pk} not found")

    return attributes_schema.dump(existing_metadata.attributes)


def add_attributes(pk, attributes):
    print(f"{pk=}")
    print(f"{attributes=}")
    existing_metadata: Metadata = Metadata.query.filter(Metadata.id == pk).one_or_none()

    if existing_metadata is None:
        abort(404, f"Metadata with id {pk} not found")

    if not attributes:
        return make_response("no attributes to add", 200)

    for attribute_data in attributes:
        if not attribute_data:
            continue
        attribute_data["metadata_id"] = pk
        new_attribute: Attribute = attribute_schema.load(attribute_data)
        new_attribute.create()
        # ! Does not check if the attribute already exists for the given metadata
    return make_response("attributes added successfully", 200)
