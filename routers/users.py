## Imports for Users Router
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from database import get_db
from schemas import PostResponse, UserCreate,  UserUpdate, UserPublic, UserPrivate,Token

from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm

from auth import (
    CurrentUser,
    create_access_token,
    hash_password,
    verify_password,
)

from config import settings


router = APIRouter()  # use for decorating routes instead of app


## Create User
@router.post(
    "",
    response_model=UserPrivate,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]
):  # db is dependency injection
    # it tells before running create_user call get_db  get session  and pass the result in db

    # we need to check if user name exist prio to user we creating                                                                       # get_db is fucntion from our database.py
    result = await db.execute(
        select(models.User).where(
            func.lower(models.User.username) == user.username.lower()
        ),  # get data from model to check add query
    )

    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    # we need to check if user email exist prio to user we creating                                                                       # get_db is fucntion from our database.py
    result = await db.execute(
        select(models.User).where(
            func.lower(models.User.email) == user.email.lower()
        ),  # get data from model to check add query
    )

    existing_email = result.scalars().first()

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )

    new_user = models.User(
        username=user.username, 
        email=user.email.lower(), # we are lower casing it because emails are case sensitive by design
        password_hash= hash_password(user.password)  # utlity from auth file
    )

    db.add(new_user)  # donot need await as its not i/o
    await db.commit()
    await db.refresh(new_user)  # db refresh the new object

    return new_user  # when we return pydnatic alreacy convert it to UserResponse model



## login_for_access_token
@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Look up user by email (case-insensitive)
    # Note: OAuth2PasswordRequestForm uses "username" field, but we treat it as email
    result = await db.execute(
        select(models.User).where(
            func.lower(models.User.email) == form_data.username.lower(),
        ),
    )
    user = result.scalars().first()

    # Verify user exists and password is correct
    # Don't reveal which one failed (security best practice)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token with user id as subject
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires,
    )
    return Token(access_token=access_token, token_type="bearer")


## get_current_user
@router.get("/me", response_model=UserPrivate)
async def get_current_user(current_user:CurrentUser):
    return current_user






# get user api
@router.get("/{user_id}", response_model=UserPublic)
async def get_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    # we need to check if user  exist
    result = await db.execute(
        select(models.User).where(
            models.User.id == user_id
        ),  # get data from model to check add query
    )

    user = result.scalars().first()

    if user:
        return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


## get_user_posts
@router.get("/{user_id}/posts", response_model=list[PostResponse])
async def get_user_posts(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.user_id == user_id)
        .order_by(models.Post.date_posted.desc())
    )
    posts = result.scalars().all()
    return posts


# update user info using patch
@router.patch("/{user_id}", response_model=UserPrivate)
async def update_user(
    user_id: int, user_update: UserUpdate, current_user:CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]
):
    # check authorization
    if user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, # 403 means you are authernticated but not allowed to update while 401 is unauthenticated
                detail="Not authorized to update the post"
            )

    # we need to check if user  exist
    result = await db.execute(
        select(models.User).where(
            models.User.id == user_id
        ),  # get data from model to check add query
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # check if coming user name is different from existing
    if user_update.username is not None and user_update.username.lower() != user.username.lower():
        result = await db.execute(
            select(models.User).where(func.lower(models.User.username) == user_update.username.lower())
        )
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )

    # check if coming email is different from existing
    if user_update.email is not None and user_update.email.lower() != user.email.lower():
        result = await db.execute(
            select(models.User).where(func.lower(models.User.email) == user_update.email.lower())
        )
        existing_email = result.scalars().first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    # we can so this same thing using setattr(user, field,value) dynamicaaly while this is manual wat of doing it
    if user_update.username is not None:
        user.username = user_update.username
    if user_update.email is not None:
        user.email = user_update.email.lower()
    if user_update.image_file is not None:
        user.image_file = user_update.image_file

    await db.commit()
    await db.refresh(user)

    return user


# delete user
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_user(user_id: int,  current_user: CurrentUser,db: Annotated[AsyncSession, Depends(get_db)]):
    
    # check authorization
    if user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, # 403 means you are authernticated but not allowed to update while 401 is unauthenticated
                detail="Not authorized to delete the post"
            )

    # we need to check if user  exist
    result = await db.execute(
        select(models.User).where(
            models.User.id == user_id
        ),  # get data from model to check add query
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    await db.delete(user)  # we need await in delete
    await db.commit()
