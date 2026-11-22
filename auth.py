from datetime import UTC, datetime, timedelta

import jwt
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash

from config import settings


password_hash= PasswordHash.recommended()   # create a password hasher recommended using argon2

oauth2_scheme= OAuth2PasswordBearer(tokenUrl="api/users/token")  # token url must match our login url path soth the OAuth2PasswordBearer extract the token header

# password hashing function
def hash_password(password: str) -> str:
    return password_hash.hash(password)

# verify password function 
# will match plain passwrd with hashed and return boolean
def verify_password(plain_password: str, hash_password: str) -> bool:
    return password_hash.verify(plain_password, hash_password)


## create_access_token
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.access_token_expire_minutes,
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key.get_secret_value(),  # getting secret key from setting
        algorithm=settings.algorithm,
    )
    return encoded_jwt


## verify_access_token
def verify_access_token(token: str) -> str | None:
    """Verify a JWT access token and return the subject (user id) if valid."""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[settings.algorithm],
            options={"require": ["exp", "sub"]},
        )
    except jwt.InvalidTokenError:
        return None
    else:
        return payload.get("sub")   # sub is userId we returb
