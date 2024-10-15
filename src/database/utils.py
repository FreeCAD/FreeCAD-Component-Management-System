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

import re
from os import path

from flask import Flask

from ..config import basedir
from ..log import logger
from .definations import db, es


def setup_db(app: Flask) -> None:
    from ..models.metadatas import Metadata
    from ..models.users import User
    from ..models.attributes import Attribute
    from ..models.files import File
    from ..models.licenses import SPDX
    from ..models.tags import Tag

    db.init_app(app)


def clear_db() -> None:
    """
    Clears the database and Elasticsearch.

    Returns:
            None
    """

    db.drop_all()
    es.options(ignore_status=[400, 404]).indices.delete(index="metadatas")
    es.options(ignore_status=[400, 404]).indices.delete(index="attributes")


def clear_data() -> None:
    """
    Clears the data in the database.

    Returns:
            None
    """

    clear_db()

    db.create_all()
    es.options(ignore_status=[400, 404]).indices.create(index="metadatas")
    es.options(ignore_status=[400, 404]).indices.create(index="attributes")


def pre_entry() -> None:
    """
    Performs pre-entry operations by creating license, tag, metadata, and file entries in the database.

    Returns:
            None
    """

    from .data.put_data import (
        db_license_entry,
        db_metadata_entry,
        db_metadata_file_entry,
        db_tags_entry,
    )

    logger.info("creating license entries...")
    db_license_entry(path.join(basedir, "database/data/spdx_license.csv"))
    logger.info("licnses entry complete")

    logger.info("creating Tag entries...")
    db_tags_entry(path.join(basedir, "database/data/tags.txt"))
    logger.info("Tags entry complete")

    logger.info("creating Metadata and Files entries...")
    db_metadata_file_entry(path.join(basedir, "database/data/files.json"))
    logger.info("Metadatas and Files entry complete")

    # logger.info("creating Component entries...")
    # db_component_entry(basedir+"app/database/data/files.json")
    # logger.info("Components entry complete")


def reset_db() -> None:
    """
    Resets the database by clearing the data and performing pre-entry operations.

    Returns:
            None
    """

    clear_data()
    pre_entry()


def make_fuzzy_query(value: str):
    """
    Creates a fuzzy query for the given value.

    Args:
            value (str): The value to be used in the fuzzy query.

    Returns:
            dict: The fuzzy query.

    Example:
            ```python
            query = make_fuzzy_query("example")
            ```
    """

    return {
        "fuzzy": {
            "name": {
                "value": value,
                "fuzziness": "AUTO",
                "transpositions": True,
                "max_expansions": 100,
                "boost": 5,
            }
        }
    }


def make_regexp_query(value: str):
    """
    Creates a fuzzy query.

    Returns:
            dict: The fuzzy query.
    """

    return {
        "regexp": {
            "name": {
                "value": value,
                "flags": "ALL",
                "case_insensitive": True,
            }
        }
    }


def make_must_query_list(search_key: str):
    """
    Creates a list of fuzzy queries based on the given search key.

    Args:
            search_key (str): The search key.

    Returns:
            list[dict]: The list of fuzzy queries.

    Example:
            ```python
            query_list = make_must_query_list("example, test")
            ```
    """

    value_list = re.split(r" |,|\||-|_|\.", search_key)
    return [make_fuzzy_query(value) for value in value_list]


def make_should_query_list(search_key: str, field: list[str]):
    """
    Creates a list of queries based on the given search key.

    Args:
            search_key (str): The search key.

    Returns:
            list[dict]: The list of queries.

    Example:
            ```python
            query_list = make_should_query_list("example, test")
            ```
    """

    value_list = re.split(r" |,|\||-|_|\.", search_key)
    query_list = [make_fuzzy_query(value) for value in value_list]
    query_list.extend(make_regexp_query(value) for value in value_list)
    query_list.append(
        {
            "more_like_this": {
                "fields": field,
                "like": search_key,
                "min_term_freq": 1,
                "max_query_terms": 12,
            }
        }
    )

    return query_list


def make_elasticsearch_query(search_key: str, field: list[str]):
    """
    Creates an Elasticsearch query based on the given search key.

    Args:
            search_key (str): The search key.

    Returns:
            dict: The Elasticsearch query.

    Example:
            ```python
            query = make_elasticsearch_query("example, test")
            ```
    """

    return {
        "bool": {
            # "must": make_must_query_list(search_key),
            "should": make_should_query_list(search_key, field),
        }
    }
