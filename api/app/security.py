import hashlib
import hmac
import secrets

import bcrypt


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def generate_token() -> str:
    return secrets.token_urlsafe(32)


def sign_token(token: str, secret: str) -> str:
    signature = hmac.new(secret.encode(), token.encode(), hashlib.sha256).hexdigest()
    return f"{token}.{signature}"


def verify_token(signed_token: str, secret: str) -> str | None:
    token, sep, signature = signed_token.rpartition(".")
    if not sep:
        return None
    expected = hmac.new(secret.encode(), token.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return None
    return token