## Imports for Posts Router
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from database import get_db
from schemas import PostCreate, PostResponse, PostUpdate
 
from auth import CurrentUser

router = APIRouter()


# json api to get all post
# endpoint to get posts and if we search using this  http://127.0.0.1:8000/api/posts we can find it
# response_model=list[PostResponse]  -> this make sure each post follow same schema or have all attributes
## get_posts
@router.get("", response_model=list[PostResponse])
async def get_posts(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .order_by(models.Post.date_posted.desc())
    )
    posts = result.scalars().all()
    return posts

 
## create_post
@router.post(
    "",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_post(post: PostCreate, current_user:CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
   
    new_post = models.Post(
        title=post.title,
        content=post.content,
        user_id=current_user.id,
    )
    db.add(new_post)
    await db.commit()
    await db.refresh(
        new_post, attribute_names=["author"]
    )  # attribute_names=["author"]  help to reload post relationship with author instead of select_inload
    return new_post


# json api to get single post
# endpoint to get a single post by a url parameters but json not html
# response_model=PostResponse ->  here we are doing same but here we don't use list as we have a single post
@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.id == post_id)
    )
    post = result.scalars().first()
    if post:
        return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


# post update put means all data will change
@router.put("/{post_id}", response_model=PostResponse)
async def update_post_full(
    post_id: int, post_data: PostCreate,current_user:CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]
):

    # =========================================================================
    # STEP 1: RETRIEVE EXISTING RESOURCE
    # Construct a SQL `SELECT * FROM posts WHERE id = post_id` statement.
    # =========================================================================

    result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()

    # Guard Clause: Short-circuit with 404 if post does not exist in database.
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    # STEP 2: FOREIGN KEY / RELATIONSHIP VALIDATION
    # Optimization: Only validate user existence if ownership (`user_id`) is changing.
    # =========================================================================
    if post.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, # 403 means you are authernticated but not allowed to update while 401 is unauthenticated
                detail="Not authorized to update the post"
            )

    # =========================================================================
    # STEP 3: IN-MEMORY STATE UPDATE
    # Update properties on the tracked ORM model instance (staged in memory session).
    # =========================================================================
    post.title = post_data.title
    post.content = post_data.content

    await db.commit()
    await db.refresh(post, attribute_names=["author"])
    return post


# post update patch means partial change
@router.patch("/{post_id}", response_model=PostResponse)
async def update_post_Partial(
    post_id: int, post_data: PostUpdate, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]
):

    result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()

    # Guard Clause: Short-circuit with 404 if post does not exist in database.
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    
    if post.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, # 403 means you are authernticated but not allowed to update while 401 is unauthenticated
                detail="Not authorized to update the post"
            )

    # since we have set default value none in schema so if data comes value will be set to none but  exclude_unset will only get value that has value so only that change
    update_data = post_data.model_dump(exclude_unset=True)

    # model dump will gave us dict so we fo for loop

    for field, value in update_data.items():
        # setattr dynamically set itel for post object by title like post.title and post.value
        setattr(post, field, value)

    await db.commit()
    await db.refresh(post, attribute_names=["author"])
    return post


# post delete route


@router.delete(
    "/{post_id}", status_code=status.HTTP_204_NO_CONTENT
)  # 204 staus mean we are not returning any response just delting the post
async def delete_post(post_id: int, current_user: CurrentUser ,db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    # Guard Clause: Short-circuit with 404 if post does not exist in database.
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    
    if post.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, # 403 means you are authernticated but not allowed to update while 401 is unauthenticated
                detail="Not authorized to delete the post"
            )

    await db.delete(post)
    await db.commit()
