from typing import Annotated

from contextlib import asynccontextmanager

from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)

from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models  # give access to the modal we created in model.py
from database import (
    Base,
    engine,
    get_db,
)  # base and engine for creating tables and get_db is a dependency fucntion that provides databse sessions


from routers import posts, users


# asynchronous way to create tables previolsy we have single line for synchronous
@asynccontextmanager
async def lifespan(_app: FastAPI):
    # startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # shutdown
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

# app amount tale three arguments first the name of directory where these static file will be avaible, second directory name and third is the name we can use in our templetes
#

app.mount("/static", StaticFiles(directory="static"), name="static")

app.mount(
    "/media", StaticFiles(directory="media"), name="media"
)  # source file from media directory where user upload imagea

# will look for template in our templates directory we made
templates = Jinja2Templates(directory="templates")


# connect routes with app

app.include_router(
    users.router, prefix="/api/users", tags=["users"]
)  # inclide_rouer connect app with router, prefix set the initial path and tag will make route section names of usrs and posts in docs
app.include_router(posts.router, prefix="/api/posts", tags=["posts"])


# response_class=HTMLResponse


# name attribute purpose is that when we clicking eithrer two of then they ahow samw /posts for both also for / so we give then distinguish name
@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")

# ---- fastapi hml template data fetching and passing
# api to get html temlplate for for all post
# we can add request that help fastapi to find template in out directory also we pass data as dict of post so that we can use it
## home
async def home(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .order_by(models.Post.date_posted.desc())
    )
    posts = result.scalars().all()
    return templates.TemplateResponse(
        request,
        "home.html",
        {"posts": posts, "title": "Home"},
    )


# note we are making two routes for each api one  for html template /posts and on for json api api/posts

# note
# response_model is a Pydantic validation layer that:
# Validates and serializes the return value into JSON
# Shows the schema in Swagger docs (/docs)
# But
# user_posts_page
# on line 87 returns a TemplateResponse — which is an HTML response rendered by Jinja2. FastAPI passes it through directly without any JSON serialization, so response_model would have no effect and would actually cause errors if applied.
# Also notice it has include_in_schema=False — it's hidden from the API docs entirely, because it's a UI page, not an API endpoint.

## post_page
# ---- fastapi hml template data fetching and passing
# api to get html temlplate for single post
# we can add request that help fastapi to find template in out directory also we pass data as dict of post so that we can use it


@app.get("/posts/{post_id}", include_in_schema=False)
async def post_page(
    request: Request, post_id: int, db: Annotated[AsyncSession, Depends(get_db)]
):
    # is the post id from data while the post_id is out varaible parameter
    # need to use selectinload here as we need to access author name
    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.id == post_id)
    )
    post = result.scalars().first()
    if post:
        # we need the title from data and only 50 characters
        title = post.title[:50]
        return templates.TemplateResponse(
            request,
            "post.html",
            {"post": post, "title": title},
        )

    # return {"error": "Post not found"} wrong way
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


## user_posts_page (for a single user post to view)
@app.get("/users/{user_id}/posts", include_in_schema=False, name="user_posts")
async def user_posts_page(
    request: Request,
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
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
    return templates.TemplateResponse(
        request,
        "user_posts.html",
        {"posts": posts, "user": user, "title": f"{user.username}'s Posts"},
    )


## login and register template_routes
@app.get("/login", include_in_schema=False)
async def login_page(request: Request):
    return templates.TemplateResponse(
        request,
        "login.html",
        {"title": "Login"},
    )


@app.get("/register", include_in_schema=False)
async def register_page(request: Request):
    return templates.TemplateResponse(
        request,
        "register.html",
        {"title": "Register"},
    )



@app.get("/account", include_in_schema=False)
async def account_page(request: Request):
    return templates.TemplateResponse(
        request,
        "account.html",
        {"title": "Account"},
    )


## StarletteHTTPException Handler
@app.exception_handler(StarletteHTTPException)
async def general_http_exception_handler(
    request: Request, exception: StarletteHTTPException
):
    message = (
        exception.detail
        if exception.detail
        else "An error occurred. Please check your request and try again."
    )

    # we will use http_exception_handler by fastapi will handel it
    if request.url.path.startswith("/api"):
        return await http_exception_handler(request, exception)

    # now message will use for template response
    message = (
        exception.detail
        if exception.detail
        else "An error occurred. Please check your request and try again."
    )
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": exception.status_code,
            "title": exception.status_code,
            "message": message,
        },
        status_code=exception.status_code,
    )


### RequestValidationError Handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exception: RequestValidationError
):
    if request.url.path.startswith("/api"):
        # we will use request_validation_exception_handler by fastapi will handel it
        return await request_validation_exception_handler(request, exception)

    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message": "Invalid request. Please check your input and try again.",
        },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
