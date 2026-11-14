## Imports for Users Router
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from database import get_db
from schemas import PostResponse, UserCreate, UserResponse, UserUpdate


router = APIRouter()  # use for decorating routes instead of app


## Create User
@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]
):  # db is dependency injection
    # it tells before running create_user call get_db  get session  and pass the result in db

    # we need to check if user name exist prio to user we creating                                                                       # get_db is fucntion from our database.py
    result = await db.execute(
        select(models.User).where(
            models.User.username == user.username
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
            models.User.email == user.email
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
        email=user.email,
    )

    db.add(new_user)  # donot need await as its not i/o
    await db.commit()
    await db.refresh(new_user)  # db refresh the new object

    return new_user  # when we return pydnatic alreacy convert it to UserResponse model


# get user api


@router.get("/{user_id}", response_model=UserResponse)
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
    )
    posts = result.scalars().all()
    return posts


# update user info using patch
@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int, user_update: UserUpdate, db: Annotated[AsyncSession, Depends(get_db)]
):
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
    if user_update.username is not None and user_update.username != user.username:
        result = await db.execute(
            select(models.User).where(models.User.username == user_update.username)
        )
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )

    # check if coming email is different from existing
    if user_update.email is not None and user_update.email != user.email:
        result = await db.execute(
            select(models.User).where(models.User.email == user_update.email)
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
        user.email = user_update.email
    if user_update.image_file is not None:
        user.image_file = user_update.image_file

    await db.commit()
    await db.refresh(user)

    return user


# delete user
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
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
