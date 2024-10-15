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

from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship, validates
from sqlalchemy.types import Float, String

from ...config import Config
from ...database import ElasticSearchBase, db
from ...database.guid import GUID
from ...database.utils import make_fuzzy_query
from ...log import logger
from ...validation import email_validator, url_validator
from ..files import File  # * Never remove this import.
from ..tags import Tag  # * Never remove this import.

metadata_tag = db.Table(
    "metadata_tag",
    Column("metadata_id", GUID(), ForeignKey("metadatas.id")),
    Column("tag_id", GUID(), ForeignKey("tags.id")),
)


class InvalidRating(Exception):
    """
    Exception class for representing an invalid rating.

    This class inherits from the `Exception` class and is used to raise an exception when an invalid rating is encountered.

    Example:
        ```python
        raise InvalidRating("Invalid rating value: 5.5")
        ```
    """


class Metadata(ElasticSearchBase):
    """
    Represents metadata for a component.

    This class inherits from `ElasticSearchBase` and defines the metadata fields for a component.
    The class includes columns for name, version, maintainer, author, thumbnail, description, rating, and license ID.
    It also defines relationships with files and tags.

    The class provides methods for adding tags and files, as well as deleting and updating the metadata.

    Example:
        ```python
        metadata = Metadata()
        metadata.name = "Component A"
        metadata.version = "1.0.0"
        metadata.maintainer = "John Doe"
        metadata.add_tag("tag1")
        metadata.add_file("file1")
        metadata.commit()
        print(metadata)
        ```
    """

    __tablename__: str = "metadatas"
    # __allow_unmapped__ = True

    name = Column(String(200), nullable=False, unique=True)
    version = Column(String(50), nullable=False)
    maintainer = Column(String(100), nullable=False)

    author = Column(String(100))
    thumbnail = Column(String(200), unique=True)
    description = Column(String(500))
    rating = Column(Float)

    license_id = Column(GUID(), ForeignKey("spdx_licenses.id"), nullable=True)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=True)
    # TODO: Add default user as freecad github

    files = relationship(
        "File", backref="metadata", cascade="all, delete, delete-orphan"
    )
    tags = relationship("Tag", secondary=metadata_tag, backref="metadatas")
    attributes = relationship(
        "Attribute", backref="metadata", cascade="all, delete, delete-orphan"
    )

    @validates("attributes")
    def validate_tool(self, key, attribute):
        assert attribute.key not in [att.name for att in self.attributes]
        return attribute

    @validates("maintainer")
    def validate_maintainer(self, key, email):
        """
        Validates the maintainer email.

        This function is a validator for the `maintainer` field in the `Metadata` class.
        It takes the `key` and `email` as arguments and validates the email using the `email_validator` function.
        If the `Config.DEBUG` flag is set to `True`, the original email is returned without validation.

        Args:
            key (str): The key of the field being validated.
            email (str): The email to validate.

        Returns:
            str: The validated email if `Config.DEBUG` is `False`, otherwise the original email.

        Example:
            ```python
            metadata = Metadata()
            metadata.maintainer = "john.doe@example.com"
            validated_email = metadata.validate_maintainer("maintainer", metadata.maintainer)
            print(validated_email)
            ```
        """

        return email_validator(email)

    @validates("author")
    def validate_author(self, key, author):
        """
        Validates the author email.

        This function is a validator for the `author` field in the `Metadata` class.
        It takes the `key` and `author` as arguments and validates the email using the `email_validator` function.
        If the `Config.DEBUG` flag is set to `True`, the original author is returned without validation.

        Args:
            key (str): The key of the field being validated.
            author (str): The author email to validate.

        Returns:
            str: The validated author email if `Config.DEBUG` is `False`, otherwise the original author email.

        Example:
            ```python
            metadata = Metadata()
            metadata.author = "john.doe@example.com"
            validated_author = metadata.validate_author("author", metadata.author)
            print(validated_author)
            ```
        """

        return email_validator(author)

    @validates("thumbnail")
    def validate_thumbnail(self, key, url):
        """
        Validates the thumbnail URL.

        This function is a validator for the `thumbnail` field in the `Metadata` class.
        It takes the `key` and `url` as arguments and validates the URL using the `url_validator` function.
        If the `Config.DEBUG` flag is set to `True`, the original URL is returned without validation.

        Args:
            key (str): The key of the field being validated.
            url (str): The URL to validate.

        Returns:
            str: The validated URL if `Config.DEBUG` is `False`, otherwise the original URL.

        Example:
            ```python
            metadata = Metadata()
            metadata.thumbnail = "https://example.com/image.jpg"
            validated_url = metadata.validate_thumbnail("thumbnail", metadata.thumbnail)
            print(validated_url)
            ```
        """

        return url_validator(url)

    @validates("rating")
    def validate_rating(self, key, rating):
        """
        Validates the rating value.

        This function is a validator for the `rating` field in the `Metadata` class.
        It takes the `key` and `rating` as arguments and checks if the rating is greater than 5.
        If the rating is greater than 5, it raises an `InvalidRating` exception.
        Otherwise, it returns the rating.

        Args:
            key (str): The key of the field being validated.
            rating (float): The rating value to validate.

        Returns:
            float: The validated rating.

        Raises:
            InvalidRating: Raised when the rating is greater than 5.

        Example:
            ```python
            metadata = Metadata()
            metadata.rating = 4.5
            validated_rating = metadata.validate_rating("rating", metadata.rating)
            print(validated_rating)
            ```
        """

        if rating > 5:
            raise InvalidRating()
        return rating

    def add_tag(self, tag):
        """
        Adds a tag to the metadata.

        This method appends the given `tag` to the `tags` list of the `Metadata` instance.
        After adding the tag, the changes are committed.

        Args:
            tag: The tag to add.

        Returns:
            None

        Example:
            ```python
            metadata = Metadata()
            metadata.add_tag("tag1")
            metadata.add_tag("tag2")
            metadata.commit()
            ```
        """

        self.tags.append(tag)
        self.commit()

    def add_file(self, file):
        """
        Adds a file to the metadata.

        This method appends the given `file` to the `files` list of the `Metadata` instance.
        After adding the file, the changes are committed.

        Args:
            file: The file to add.

        Returns:
            None

        Example:
            ```python
            metadata = Metadata()
            metadata.add_file("file1")
            metadata.add_file("file2")
            metadata.commit()
            ```
        """

        self.files.append(file)
        self.commit()

    def add_attribute(self, attribute: dict):
        self.attributes.append(attribute)
        self.commit()

    def delete(self):
        """
        Deletes the metadata.

        This method calls the `delete` method of the superclass, passing the `"name"` key and the `name` attribute of the instance.

        Returns:
            The result of the `delete` method.

        Example:
            ```python
            metadata = Metadata()
            result = metadata.delete()
            print(result)
            ```
        """

        return super().delete("name", self.name)

    def update(self):
        """
        Updates the metadata.

        This method calls the `update` method of the superclass, passing the `"name"` key and the `name` attribute of the instance.

        Returns:
            The result of the `update` method.

        Example:
            ```python
            metadata = Metadata()
            result = metadata.update()
            print(result)
            ```
        """

        return super().update("name", self.name)

    def __repr__(self) -> str:
        return f'<Metadata "{self.name}">'

    @classmethod
    def elasticsearch(cls, search_key: str) -> set[str]:
        """
        Performs an Elasticsearch search based on the specified search key and returns a set of matching names.

        Args:
            search_key: The key to search for.

        Returns:
            set[str]: A set of matching names.
        """

        search_key += " "
        match: str = re.findall(r"([\w ]*)[^\w:][\w*:.*$]*", search_key)[0]

        # value_list = re.split(r" |,|\||-|_|\.", search_key)
        query_list = [make_fuzzy_query(value) for value in match.split(" ")]
        # query_list.extend(make_regexp_query(value) for value in value_list)
        query_list.append(
            {
                "more_like_this": {
                    "fields": ["name"],
                    "like": match,
                    "min_term_freq": 1,
                    "max_query_terms": 12,
                }
            }
        )

        query = {
            "bool": {
                "should": query_list,
            }
        }
        response = super().elasticsearch(cls.__tablename__, query)

        return {hit["_source"]["name"] for hit in response["hits"]["hits"]}
