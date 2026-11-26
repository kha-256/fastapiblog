from datetime import UTC, datetime, timedelta

import jwt
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash

from config import settings

from typing import Annotated
from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import models
from database import get_db


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


# will use verify access token here
# every route that uses this dependency will automatically check token validity and get full user object
## get_current_user
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],  # get token from header
    db: Annotated[AsyncSession, Depends(get_db)],   # need session to execute databse query
) -> models.User:
    user_id = verify_access_token(token)   #get userid from token
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id_int = int(user_id)   # convert userid to integer as it is string in token
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(
        select(models.User).where(models.User.id == user_id_int), # find user from database table and return user object
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# as get_current_user is use in route so intead of repeating code like this in every route
# ❌ Without Annotated — repetitive in every route
# def get_me(user: models.User = Depends(get_current_user)):
#    ...
#def update_me(user: models.User = Depends(get_current_user)):

# we will use DRY priciple hete define once and will use just user:CurrentUser
# as get_current_user return user object so we pass models.User as type hint as it will hanle type valistion for data
CurrentUser= Annotated[models.User, Depends(get_current_user)]