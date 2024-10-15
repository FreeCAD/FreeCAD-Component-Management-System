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

from functools import lru_cache

from github import ContentFile, Github, Repository

from ...log import logger


@lru_cache
def github(access_token):
    return Github(access_token)


@lru_cache
def get_repository(access_token, repository) -> Repository.Repository:
    """
    Returns a repository object for the given access token and repository name.

    This function uses the `Github` class from the `pygithub` library to authenticate with the provided access token and retrieve the specified repository. The repository object is then returned.

    Args:
        access_token (str): The access token for authentication.
        repository (str): The name of the repository.

    Returns:
        Repository: The repository object.

    Example:
        ```python
        access_token = "your_access_token"
        repository_name = "your_repository"
        repo = get_repository(access_token, repository_name)
        print(repo.name)
        ```
    """

    g = github(access_token)
    return g.get_user().get_repo(repository)


def update_file(
    repository: Repository.Repository, branch, raw_file_data, destination_file_path
) -> ContentFile.ContentFile:
    """
    Updates a file in the repository with the provided raw file data.

    This function retrieves all files in the repository and checks if the destination file path exists. If the destination file path is found, the file is updated with the raw file data. The updated file content is returned.

    Args:
        repository (Repository): The repository object.
        branch (str): The branch name.
        raw_file_data (bytes): The raw file data to update.
        destination_file_path (str): The destination file path.

    Returns:
        ContentFile: The updated file content.

    Raises:
        FileNotFoundError: If the destination file path is not found.

    Example:
        ```python
        repository = get_repository(access_token, repository_name)
        branch = "main"
        raw_file_data = b"Updated file content"
        destination_file_path = "path/to/file.txt"
        updated_file = update_file(repository, branch, raw_file_data, destination_file_path)
        print(updated_file.path)
        ```
    """

    all_files = []
    contents: list[ContentFile.ContentFile] = repository.get_contents("")

    while contents:
        file_content = contents.pop(0)
        if file_content.type == "dir":
            contents.extend(repository.get_contents(file_content.path))
        else:
            file = file_content
            all_files.append(
                str(file).replace('ContentFile(path="', "").replace('")', "")
            )

    if destination_file_path not in all_files:
        raise FileNotFoundError("The destination file path for found")

    contents = repository.get_contents(destination_file_path)

    return repository.update_file(
        contents.path,
        "committing files",
        raw_file_data,
        contents.sha,
        branch=branch,
    )["content"]


def upload_new_file(
    repository: Repository.Repository, branch, raw_file_data, destination_file_path
) -> ContentFile.ContentFile:
    """
    Uploads a new file to the repository with the provided raw file data.

    This function creates a new file in the repository with the specified destination file path and raw file data. The file is committed with the given branch name. The content of the uploaded file is returned.

    Args:
        repository (Repository): The repository object.
        branch (str): The branch name.
        raw_file_data (bytes): The raw file data to upload.
        destination_file_path (str): The destination file path.

    Returns:
        ContentFile: The content of the uploaded file.

    Example:
        ```python
        repository = get_repository(access_token, repository_name)
        branch = "main"
        raw_file_data = b"New file content"
        destination_file_path = "path/to/new_file.txt"
        uploaded_file = upload_new_file(repository, branch, raw_file_data, destination_file_path)
        print(uploaded_file.path)
        ```
    """
    logger.info(f"Uploading new file to {destination_file_path}")

    return repository.create_file(
        destination_file_path,
        "committing files",
        raw_file_data,
        branch=branch,
    )["content"]
