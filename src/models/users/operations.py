import jwt
from flask import request
from ...authentication.utils import decode_auth_token
from ...log import logger
from .models import User
from ..components.schema import components_schema
from ..metadatas.schemas import metadatas_schema


def read_user_components():
    """
    Returns the components associated with the user.

    This function retrieves all components associated with the user from the database and returns them.

    Args:
                    user_id (int): The user ID.

    Returns:
                    list[Component]: The components associated with the user.

    Example:
                    ```python
                    user_id = 1
                    components = user_components(user_id)
                    for component in components:
                                    print(component.name)
                    ```
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
    metadatas = user.metadatas
    serialized_metadatas = metadatas_schema.dump(metadatas)
    serialized_components = components_schema.dump(metadatas)
    result = []
    for component, metadata in zip(serialized_components, serialized_metadatas):
        if len(component["files"]) < 1:
            continue
        component["metadata"] = metadata
        result.append(component)

    return result
