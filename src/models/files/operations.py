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

from pathlib import Path
from typing import Literal

from flask import Response, abort, make_response, request
from werkzeug.datastructures import FileStorage

from ..metadatas import Metadata, metadata_schema
from ..utils import PsudoPagination, paginated_schema
from ..utils.pagination import MAX_PER_PAGE
from .models import File, FileType
from .schemas import file_schema, files_schema
from .utils import get_repository, upload_new_file


def read_all():
    """
    Reads all files from the database and returns them in a paginated format.

    This function queries all files from the database using `File.query.all()`. It then creates a pseudo-pagination object using `PsudoPagination` and the queried files. The paginated result is serialized using `files_schema` and returned.

    Returns:
            dict: The paginated result of all files.

    Example:
            ```python
            result = read_all()
            print(result)
            ```
    """

    query: list[File] = File.query.all()
    psudo_paged_query = PsudoPagination(0, None, query, len(query))
    return paginated_schema(files_schema).dump(psudo_paged_query)


def read_page(page=None, page_size=None) -> list[dict[str, str]]:
    """
    Reads a page of files from the database and returns them in a paginated format.

    If both `page` and `page_size` are not provided, it calls the `read_all()` function to retrieve all files. Otherwise, it queries the files using pagination parameters `page` and `page_size` with a maximum per page limit of `MAX_PER_PAGE`. The paginated result is serialized using `files_schema` and returned.

    Args:
            page (int, optional): The page number. Defaults to None.
            page_size (int, optional): The number of items per page. Defaults to None.

    Returns:
            list[dict[str, str]]: The paginated result of files.

    Example:
            ```python
            result = read_page(page=1, page_size=10)
            print(result)
            ```
    """

    if not all((page, page_size)):
        return read_all()

    query = File.query.paginate(
        page=page, per_page=page_size, max_per_page=MAX_PER_PAGE
    )
    return paginated_schema(files_schema).dump(query)


def read_one(pk) -> tuple[dict[str, str], Literal[200]]:
    """
    Reads a single file from the database based on the provided primary key (pk).

    This function queries the file with the specified primary key using `File.query.filter(File.id==pk).one_or_none()`. If the file is not found, it raises a 404 error with a corresponding message. Otherwise, it serializes the file using `file_schema` and returns it along with the HTTP status code 200.

    Args:
            pk: The primary key of the file.

    Returns:
            tuple[dict[str, str], Literal[200]]: A tuple containing the serialized file and the HTTP status code 200.

    Raises:
            HTTPException: If the file with the specified primary key is not found.

    Example:
            ```python
            result = read_one(1)
            print(result)
            ```
    """

    file: File | None = File.query.filter(File.id == pk).one_or_none()

    if file is None:
        abort(404, f"File with id {pk} not found!")

    return file_schema.dump(file), 200


def create(file_data, metadata_id=None) -> tuple[dict[str, str], Literal[201]]:
    """
    Creates a new file with the provided file data and optional metadata ID.

    Args:
            file_data (dict): The file data.
            metadata_id (int, optional): The metadata ID. Defaults to None.

    Returns:
            tuple[dict[str, str], Literal[201]]: A tuple containing the serialized new file and the HTTP status code 201.

    Raises:
            HTTPException: If a file with the same URL already exists.

    Example:
            ```python
            file_data = {
                    "url": "https://example.com/file.txt",
                    "type": "text/plain"
            }
            metadata_id = 123
            result = create(file_data, metadata_id)
            print(result)
            ```
    """

    url = file_data.get("url")

    file_data["type"] = FileType.serialize(file_data.get("type"))

    existing_file: File | None = File.query.filter(File.url == url).one_or_none()

    if existing_file is not None:
        abort(406, f"File with url:{url} already exists")

    if metadata_id is not None:
        file_data["metadata_id"] = metadata_id

    new_file: File = file_schema.load(file_data)
    new_file.create()

    return file_schema.dump(new_file), 201


def delete(pk) -> Response:
    """
    Deletes a file from the database based on the provided primary key (pk).

    Args:
            pk: The primary key of the file.

    Returns:
            Response: A response indicating the successful deletion of the file.

    Raises:
            HTTPException: If the file with the specified primary key is not found.

    Example:
            ```python
            result = delete(1)
            print(result)
            ```
    """

    existing_file: File | None = File.query.filter(File.id == pk).one_or_none()

    if existing_file is None:
        abort(404, f"File with id {pk} not found")

    existing_file.delete()
    return make_response(f"{existing_file.url}:{pk} successfully deleted", 200)


def upload_to_github(upload_info):
    """
    Uploads files and a thumbnail image to a GitHub repository and updates the metadata.

    Args:
                    upload_info (dict): The upload information.

    Returns:
                    tuple[dict, Literal[201]]: A tuple containing the response dictionary and the HTTP status code 201.

    Raises:
                    HTTPException: If the metadata with the specified ID is not found.

    Example:
                    ```python
                    upload_info = {
                                    "metadata_id": 123,
                                    "branch": "main",
                                    "repository": "my-repo"
                    }
                    result = upload_to_github(upload_info)
                    print(result)
                    ```
    """

    files = request.files.getlist("component_files")
    thumbnail_file: FileStorage = request.files.get("thumbnail_image")
    access_token = request.headers.get("X-Access-Token", "")

    metadata: Metadata | None = Metadata.query.filter(
        Metadata.id == upload_info.get("metadata_id")
    ).one_or_none()
    if metadata is None:
        abort(404, f"Metadata with id {upload_info.get('metadata_id')} not found")

    repo = get_repository(access_token, upload_info.get("repository"))

    response = {
        "files": [],
        "metadata": None,
    }
    for file in files:
        content = upload_new_file(
            repo,
            upload_info.get("branch"),
            file.stream.read(),
            f"{metadata.name}/{file.filename.rsplit('/', 1)[-1]}",
        )

        resp, _ = create(
            {
                "metadata_id": str(metadata.id),
                "size": content.size,
                "type": file.filename.rsplit(".", 1)[-1],
                "url": content.download_url,
            }
        )
        response["files"].append(resp)

    if thumbnail_file is not None:
        content = upload_new_file(
            repo,
            upload_info.get("branch"),
            thumbnail_file.stream.read(),
            f"{metadata.name}/thumbnail{Path(thumbnail_file.filename).suffix}",
        )
        metadata.thumbnail = content.download_url
    else:
        metadata.thumbnail = None
    metadata.commit()
    response["metadata"] = metadata_schema.dump(metadata)

    return response, 201
