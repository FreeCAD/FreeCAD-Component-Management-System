import datetime

import jwt
import requests

from ..config import Config
from ..log import logger


def encode_auth_token(user_id) -> str:
    """
    Generate the JWT authentication token for the user.
    """
    payload = {
        "exp": datetime.datetime.now() + datetime.timedelta(hours=1),
        "iat": datetime.datetime.now(),
        "sub": str(user_id),
    }
    return jwt.encode(payload, Config.FLASK_SECRET, algorithm="HS256")


def decode_auth_token(auth_token):
    """
    Decode the JWT authentication token and return the user ID.
    """
    payload = jwt.decode(auth_token, Config.FLASK_SECRET, algorithms=["HS256"])
    return payload["sub"]


def exchange_code_for_token(code: str):
    """
    Exchange the github authentication code for an github access token.
    """
    if not code:
        raise ValueError("The authentication code has to be supplied!")

    if Config.GITHUB_OAUTH_CLIENT_ID is None:
        raise ValueError("The GitHub OAuth Client ID has to be supplied!")

    if Config.GITHUB_OAUTH_CLIENT_SECRET is None:
        raise ValueError("The GitHub OAuth Client Secret has to be supplied!")

    response = requests.post(
        "https://github.com/login/oauth/access_token",
        data={
            "client_id": Config.GITHUB_OAUTH_CLIENT_ID,
            "client_secret": Config.GITHUB_OAUTH_CLIENT_SECRET,
            "code": code,
        },
        headers={"Accept": "application/json"},
        timeout=10,
    )

    if response.status_code == 200:
        return response.json().get("access_token")


def get_github_user(auth_token: str):
    """
    Get the user details from the GitHub API using the access token.
    """
    if not auth_token:
        raise ValueError("The authentication token has to be supplied!")

    response = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"token {auth_token}"},
        timeout=10,
    )

    logger.debug(f"token provided: {auth_token}")
    logger.debug(f"GitHub API response: {response.json()}")

    if response.status_code == 200:
        return response.json()
