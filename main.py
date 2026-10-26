from typing import Annotated

from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from sqlalchemy import select
from sqlalchemy.orm import Session

import models     # give access to the modal we created in model.py
from database import Base, engine, get_db  # base and engine for creating tables and get_db is a dependency fucntion that provides databse sessions


from schemas import PostCreate, PostResponse, UserCreate, UserResponse


Base.metadata.create_all(bind=engine)  # need to at top
                                       # look into all our model and create tables if dont exist and its item potent mean save to run multiple times

app = FastAPI() 

# app amount tale three arguments first the name of directory where these static file will be avaible, second directory name and third is the name we can use in our templetes
#

app.mount('/static', StaticFiles(directory='static'), name='static')

app.mount("/media", StaticFiles(directory="media"),name="media")  # source file from media directory where user upload imagea 

# will look for template in our templates directory we made
templates = Jinja2Templates(directory="templates")

# dummy data as dict
# posts: list[dict] = [
#     {
#         "id": 1,
#         "author": "Khadija Noor",
#         "title": "FastAPI is Awesome",
#         "content": "This framework is really easy to use and super fast.",
#         "date_posted": "April 20, 2025",
#     },
#     {
#         "id": 2,
#         "author": "Jane Doe",
#         "title": "Python is Great for Web Development",
#         "content": "Python is a great language for web development, and FastAPI makes it even better.",
#         "date_posted": "April 21, 2025",
#     },
# ]


# =================================== Video 1 content ========================================



# #decorator and we are decorating home function with it its base route
# @app.get("/")
# def home():
#   return {"message":"Hello World!!"}

#decorator and we are decorating home function with it its base route but with html response
# @app.get("/", response_class=HTMLResponse, include_in_schema=False)
# @app.get("/posts", response_class=HTMLResponse, include_in_schema=False)
#if we want same thing on different rout we can do by using multiple decorators so on / and on /post same thing will dsiplay
# def home():
#   return f"<h1>{posts[0]['title']}</h1>"

#enpoint to get posts and if we search using this  http://127.0.0.1:8000/api/posts we can find it
# @app.get("/api/posts")
# def get_post():
#     return posts




# =================================== Video 2 content ========================================


# response_class=HTMLResponse


# name attribute purpose is that when we clicking eithrer two of then they ahow samw /posts for both also for / so we give then distinguish name
@app.get("/",  include_in_schema=False, name='home')
@app.get("/posts",  include_in_schema=False, name='post')

#---- fastapi hml template data fetching and passing
# api to get html temlplate for for all post
# we can add request that help fastapi to find template in out directory also we pass data as dict of post so that we can use it
def home(request: Request):
  return templates.TemplateResponse(
    request,
    "home.html", 
    {
        "posts": posts, 
        "title": "Home"
    })



# note we are making two routes for each api one  for html template /posts and on for json api api/posts

#---- fastapi hml template data fetching and passing
# api to get html temlplate for single post
# we can add request that help fastapi to find template in out directory also we pass data as dict of post so that we can use it
@app.get("/posts/{post_id}",  include_in_schema=False)
def post_page(request: Request, post_id: int):
    for post in posts:
        # is the post id from data while the post_id is out varaible parameter
        if post.get("id") == post_id:
            #we need the title from data and only 50 characters
            title= post["title"][:50]
            return templates.TemplateResponse(
                request,
                "post.html",
                 {
                    "post": post, 
                    "title": title
                 })
     # return {"error": "Post not found"} wrong way
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


## Create User
@app.post(
    "/api/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)

def create_user(user: UserCreate, db: Annotated[Session, Depends(get_db)]):   # db is dependency injection
                                                                              # it tells before running create_user call get_db  get session  and pass the result in db
    
    # we need to check if user name exist prio to user we creating                                                                       # get_db is fucntion from our database.py
    result= db.execute(
        select(models.User).where(models.User.username == user.username),    # get data from model to check add query
        )          

    existing_user = result.scalar().first

    if existing_user:
        raise HTTPException(
            status_code= status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )   


    # we need to check if user email exist prio to user we creating                                                                       # get_db is fucntion from our database.py
    result= db.execute(
        select(models.User).where(models.User.email == user.email),    # get data from model to check add query
        )          

    existing_email = result.scalar().first

    if existing_email:
        raise HTTPException(
            status_code= status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )  

     new_user = models.User(
        username= user.username,
        email= user.email,
     )   

     db.add(new_user)
     db.commit()
     db.refresh(new_user)    # db refresh the new object   

     return new_user  # when we return pydnatic alreacy convert it to UserResponse model                                          
                                                                    

# get user api

@app.get("/api/users/{user_id}", response_model=PostResponse)
def get_user(user_id: int,db: Annotated[Session, Depends(get_db)]):   
      # we need to check if user  exist                                                                      
    result= db.execute(
        select(models.User).where(models.User.id == user_id),    # get data from model to check add query
        )        

     user= result.scalars().first()

     if user:
        return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")      


                                                      
## get_user_posts
@app.get("/api/users/{user_id}/posts", response_model=list[PostResponse])
def get_user_posts(user_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    result = db.execute(select(models.Post).where(models.Post.user_id == user_id))
    posts = result.scalars().all()
    return posts



















# # json api to get all post
# #endpoint to get posts and if we search using this  http://127.0.0.1:8000/api/posts we can find it
# @app.get("/api/posts",)
# def get_posts():
#     return posts 


# json api to get all post
#endpoint to get posts and if we search using this  http://127.0.0.1:8000/api/posts we can find it
# response_model=list[PostResponse]  -> this make sure each post follow same schema or have all attributes 
@app.get("/api/posts", response_model=list[PostResponse])
def get_posts():
    return posts 


    ## Create Post
@app.post(
    "/api/posts",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_post(post: PostCreate):
    new_id = max(p["id"] for p in posts) + 1 if posts else 1
    new_post = {
        "id": new_id,
        "author": post.author,
        "title": post.title,
        "content": post.content, 
        "date_posted": "April 23, 2025",
    }
    posts.append(new_post)
    return new_post


# json api to get single post
#endpoint to get a single post by a url parameters but json not html
# response_model=PostResponse ->  here we are doing same but here we don't use list as we have a single post
@app.get("/api/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: int):
    for post in posts:
        if post.get("id") == post_id:
          return post
    # return {"error": "Post not found"} wrong way
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")




## StarletteHTTPException Handler
@app.exception_handler(StarletteHTTPException)
def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    message = (
        exception.detail
        if exception.detail
        else "An error occurred. Please check your request and try again."
    )

    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exception.status_code,
            content={"detail": message},
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
def validation_exception_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": exception.errors()},
        )
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




