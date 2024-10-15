from ..models.users import User
from .utils import encode_auth_token, exchange_code_for_token, get_github_user


def sign_up(github_token):
    """
    Sign up a new user.
    """
    user_data = get_github_user(github_token)
    user = User(username=user_data["login"])
    user.save()
    return encode_auth_token(user.id)


def sign_in(github_token) -> str:
    """
    Login a user and returns JWT.
    """
    user_data = get_github_user(github_token)
    user = User.query.filter_by(username=user_data["login"]).first()
    return encode_auth_token(user.id)
