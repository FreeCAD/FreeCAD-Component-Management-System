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

import uuid
from typing import Any

from marshmallow_sqlalchemy.schema import SQLAlchemyAutoSchema
from sqlalchemy.orm import Session

from .definations import db, es
from .guid import GUID
from .utils import make_elasticsearch_query


class Base(db.Model):
    """
    Base class for database models.

    Attributes:
        __abstract__ (bool): Indicates if the class is abstract.
        __session (Session): The database session.
        id (Column): The primary key column.
        created_at (Column): The column for storing the creation timestamp.
        updated_at (Column): The column for storing the update timestamp.

    Methods:
        create(): Adds the instance to the session and commits the changes.
        update(): Commits the changes to the session.
        delete(): Deletes the instance from the session and commits the changes.
        commit(): Commits the changes to the session.
    """

    __abstract__ = True

    __session: Session = db.session

    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )

    def create(self) -> None:
        """
        Adds the instance to the session and commits the changes.

        Args:
            self: The instance to be added to the session.

        Returns:
            None
        """

        self.__session.add(self)
        self.commit()

    def update(self) -> None:
        """
        Commits the changes to the session.

        Args:
            self: The instance to be updated.

        Returns:
            None
        """

        self.commit()

    def delete(self) -> None:
        """
        Deletes the instance from the session and commits the changes.

        Args:
            self: The instance to be deleted.

        Returns:
            None
        """

        self.__session.delete(self)
        self.commit()

    def commit(self) -> None:
        """
        Commits the changes to the session.

        Args:
            self: The instance to be committed.

        Returns:
            None
        """

        self.__session.commit()


class ElasticSearchBase(Base):
    """
    Abstract base class for Elasticsearch models.

    Attributes:
        __abstract__ (bool): Indicates if the class is abstract.
        __es: The Elasticsearch client.
        __schema (SQLAlchemyAutoSchema): The schema for a single instance.
        __schema_many (SQLAlchemyAutoSchema): The schema for multiple instances.

    Methods:
        __init__(*args, **kwargs): Initializes the ElasticsearchBase instance.
        create(): Creates a new instance in the database and indexes it in Elasticsearch.
        update(field_name, value): Updates the instance in the database and Elasticsearch based on the specified field and value.
        delete(field_name, value): Deletes the instance from the database and Elasticsearch based on the specified field and value.
        elasticsearch(search_key): Performs an Elasticsearch search and returns a set of matching names.
        set_schemas(schema, schema_many): Sets the schemas for the ElasticsearchBase class.
    """

    __abstract__ = True

    __es = es
    __schema: SQLAlchemyAutoSchema
    __schema_many: SQLAlchemyAutoSchema

    def __init__(self, *args, **kwargs) -> None:
        """
        Initializes the ElasticsearchBase instance.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            None
        """

        super().__init__(*args, **kwargs)
        self.__es.options(ignore_status=[400, 404]).indices.create(
            index=self.__tablename__
        )

    def create(self) -> None:
        """
        Creates a new instance in the database and indexes it in Elasticsearch.

        Raises:
            Exception: If an error occurs during the creation process.

        Returns:
            None
        """

        try:
            super().create()
        except:
            raise

        doc = self.__schema.dump(self)
        self.__es.index(index=self.__tablename__, document=doc)

    def update(self, field_name, value) -> None:
        """
        Updates the instance in the database and Elasticsearch based on the specified field and value.

        Args:
            field_name: The name of the field to match.
            value: The value to match.

        Raises:
            Exception: If an error occurs during the update process.

        Returns:
            None
        """

        try:
            super().update()
        except:
            raise

        sq = self.__es.search(
            index=self.__tablename__, query={"match": {field_name: value}}
        )

        self.__es.update(
            index="index_name",
            id=sq["hits"]["hits"]["_id"],
            doc=self.__schema.dump(self),
        )

    def delete(self, field_name: str, value: Any) -> None:
        """
        Deletes the instance from the database and Elasticsearch based on the specified field and value.

        Args:
            field_name: The name of the field to match.
            value: The value to match.

        Raises:
            Exception: If an error occurs during the deletion process.

        Returns:
            None
        """

        try:
            super().delete()
        except:
            raise
        self.__es.delete_by_query(index=self.__tablename__, q={field_name: value})

    @classmethod
    def elasticsearch(cls, index, query):
        """
        Performs an Elasticsearch search based on the specified search key and returns a set of matching names.

        Args:
            search_key: The key to search for.

        Returns:
            set[str]: A set of matching names.
        """

        return cls.__es.search(
            index=index,
            query=query,
        )

    @classmethod
    def set_schemas(
        cls, schema: SQLAlchemyAutoSchema, schema_many: SQLAlchemyAutoSchema
    ) -> None:
        """
        Sets the schemas for the ElasticsearchBase class.

        Args:
            schema: The schema for a single instance.
            schema_many: The schema for multiple instances.

        Returns:
            None
        """

        cls.__schema = schema
        cls.__schema_many = schema_many
