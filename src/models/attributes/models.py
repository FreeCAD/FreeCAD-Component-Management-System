import re

from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.types import String

from ...database import ElasticSearchBase
from ...database.guid import GUID
from ...log import logger


class Attribute(ElasticSearchBase):
    """
    Represents an attribute of a component.

    This class inherits from `ElasticSearchBase` and provides a method for performing an Elasticsearch search
    based on a specified search key. It returns a set of matching names.

    Args:
        search_key (str): The key to search for.

    Returns:
        set[str]: A set of matching names.
    """

    __tablename__: str = "attributes"
    __allow_unmapped__ = True

    key = Column(String(50), nullable=False)
    value = Column(String(200))

    metadata_id = Column(GUID(), ForeignKey("metadatas.id"), nullable=False)

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
        pairs: dict[str, str] = {
            x.split(":")[0].replace("_", " "): x.split(":")[1].replace("_", " ")
            for x in re.findall(r"(\w+:\w+)", search_key)
        }
        keys_only: list[str] = [
            item.replace("_", " ") for item in re.findall(r"(\w+):[^\w]", search_key)
        ]
        values_only: list[str] = [
            item.replace("_", " ") for item in re.findall(r"[^\w]:(\w+)", search_key)
        ]
        # working in (\w* [\w]+:)[^:\w*] for values that catches values that has space(char) in them
        logger.debug(f"{pairs=}")
        logger.debug(f"{keys_only=}")
        logger.debug(f"{values_only=}")

        should_queries = []

        if pairs:
            should_queries.extend(
                [
                    {"terms": {"key.keyword": list(pairs.keys())}},
                    {"terms": {"value.keyword": list(pairs.values())}},
                ]
            )
        if keys_only:
            should_queries.append(
                {"terms": {"key.keyword": keys_only}},
            )
        if values_only:
            should_queries.append(
                {"terms": {"value.keyword": values_only}},
            )
        # ! when empty list is passed to must, it returns all the attributes
        query = {
            "bool": {
                "should": should_queries,
            },
        }

        response = super().elasticsearch(cls.__tablename__, query)
        logger.debug(f"{response=}")
        return {hit["_source"]["metadata_id"] for hit in response["hits"]["hits"]}
