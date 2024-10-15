from flask import request
from ..models.users import User
from .utils import (
    encode_auth_token,
    exchange_code_for_token,
    get_github_user,
)

from src.log import logger


def auth_with_access_token():  # -> tuple[Literal['No access token received'], Literal[400]] ...:
    access_token = request.headers.get("X-Access-Token")
    if not access_token:
        return "No access token received", 400

    user_data = get_github_user(access_token)
    user = User.query.filter_by(username=user_data["login"]).first()

    if not user:
        user = User(username=user_data["login"], admin=False)
        user.create()
    jwt = encode_auth_token(str(user.id))
    logger.debug(f"{jwt=}")
    return {
        "jwt": jwt,
    }, 200


def github_oauth_callback():
    code = request.args.get("code")
    if not code:
        return "No code received", 400

    auth_token = exchange_code_for_token(code)

    if auth_token is None:
        return "Could not authenticate with GitHub", 400

    user_data = get_github_user(auth_token)
    user = User.query.filter_by(username=user_data["login"]).first()

    if not user:
        user = User(username=user_data["login"], admin=False)
        user.create()

    return {
        "github_auth_token": auth_token,
        "jwt": encode_auth_token(user.id),
    }, 200
