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


from schemas import PostCreate, PostResponse, UserCreate, UserResponse, PostUpdate, UserUpdate


Base.metadata.create_all(bind=engine)  # need to at top
                                       # look into all our model and create tables if dont exist and its item potent mean save to run multiple times

app = FastAPI() 

# app amount tale three arguments first the name of directory where these static file will be avaible, second directory name and third is the name we can use in our templetes
#

app.mount('/static', StaticFiles(directory='static'), name='static')

app.mount("/media", StaticFiles(directory="media"),name="media")  # source file from media directory where user upload imagea 

# will look for template in our templates directory we made
templates = Jinja2Templates(directory="templates")



# response_class=HTMLResponse


# name attribute purpose is that when we clicking eithrer two of then they ahow samw /posts for both also for / so we give then distinguish name
@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")

#---- fastapi hml template data fetching and passing
# api to get html temlplate for for all post
# we can add request that help fastapi to find template in out directory also we pass data as dict of post so that we can use it
## home
def home(request: Request, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post))
    posts = result.scalars().all()
    return templates.TemplateResponse(
        request,
        "home.html",
        {"posts": posts, "title": "Home"},
    )


# note we are making two routes for each api one  for html template /posts and on for json api api/posts

# note 
#response_model is a Pydantic validation layer that:
# Validates and serializes the return value into JSON
# Shows the schema in Swagger docs (/docs)
#But 
# user_posts_page
# on line 87 returns a TemplateResponse — which is an HTML response rendered by Jinja2. FastAPI passes it through directly without any JSON serialization, so response_model would have no effect and would actually cause errors if applied.
# Also notice it has include_in_schema=False — it's hidden from the API docs entirely, because it's a UI page, not an API endpoint.

 ## post_page
#---- fastapi hml template data fetching and passing
# api to get html temlplate for single post
# we can add request that help fastapi to find template in out directory also we pass data as dict of post so that we can use it

@app.get("/posts/{post_id}", include_in_schema=False)
def post_page(request: Request, post_id: int, db: Annotated[Session, Depends(get_db)]):
    # is the post id from data while the post_id is out varaible parameter
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if post:
         #we need the title from data and only 50 characters
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
def user_posts_page(
    request: Request,
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    result = db.execute(select(models.Post).where(models.Post.user_id == user_id))
    posts = result.scalars().all()
    return templates.TemplateResponse(
        request,
        "user_posts.html",
        {"posts": posts, "user": user, "title": f"{user.username}'s Posts"},
    )



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

    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(
            status_code= status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )   


    # we need to check if user email exist prio to user we creating                                                                       # get_db is fucntion from our database.py
    result= db.execute(
        select(models.User).where(models.User.email == user.email),    # get data from model to check add query
        )          

    existing_email = result.scalars().first()

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

@app.get("/api/users/{user_id}", response_model=UserResponse)
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


# update user info using patch
@app.patch("/api/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int,user_update: UserUpdate, db: Annotated[Session, Depends(get_db)]):   
      # we need to check if user  exist                                                                      
    result= db.execute(
        select(models.User).where(models.User.id == user_id),    # get data from model to check add query
        )        
    user= result.scalars().first()
    if not user:
       raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND, 
          detail="User not found"
          ) 


    # check if coming user name is different from existing
    if user_update.username is not None and user_update.username != user.username:
       result =  db.execute(
        select(models.User).where(models.User.username == user_update.username)
        )    
       existing_user= result.scalars().first()
       if existing_user:
            raise HTTPException(
          status_code=status.HTTP_400_BAD_REQUEST, 
          detail="Username already exists"
          )

    # check if coming email is different from existing
    if user_update.email is not None and user_update.email != user.email:
       result =  db.execute(
        select(models.User).where(models.User.email == user_update.email)
        )    
       existing_email= result.scalars().first()
       if existing_email:
            raise HTTPException(
          status_code=status.HTTP_400_BAD_REQUEST, 
          detail="Email already registered"
          )


    # we can so this same thing using setattr(user, field,value) dynamicaaly while this is manual wat of doing it
    if user_update.username is not None:
        user.username= user_update.username
    if user_update.email is not None:
        user.email= user_update.email
    if user_update.image_file is not None:
        user.image_file= user_update.image_file

    
    db.commit()
    db.refresh(user)

    return user


#delete user
@app.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def update_user(user_id: int, db: Annotated[Session, Depends(get_db)]):   
    # we need to check if user  exist                                                                      
    result= db.execute(
        select(models.User).where(models.User.id == user_id),    # get data from model to check add query
        )        
    user= result.scalars().first()
    if not user:
       raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND, 
          detail="User not found"
          ) 


    db.delete(user)
    db.commit()



# json api to get all post
#endpoint to get posts and if we search using this  http://127.0.0.1:8000/api/posts we can find it
# response_model=list[PostResponse]  -> this make sure each post follow same schema or have all attributes 
## get_posts
@app.get("/api/posts", response_model=list[PostResponse])
def get_posts(db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post))
    posts = result.scalars().all()
    return posts


 ## Create Post
## create_post
@app.post(
    "/api/posts",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_post(post: PostCreate, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == post.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    new_post = models.Post(
        title=post.title,
        content=post.content,
        user_id=post.user_id,
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post


# json api to get single post
#endpoint to get a single post by a url parameters but json not html
# response_model=PostResponse ->  here we are doing same but here we don't use list as we have a single post
@app.get("/api/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if post:
        return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")




#post update put means all data will change
@app.put("/api/posts/{post_id}", response_model=PostResponse)
def update_post_full(
    post_id: int, 
    post_data: PostCreate,
    db: Annotated[Session, Depends(get_db)]):

    # =========================================================================
    # STEP 1: RETRIEVE EXISTING RESOURCE
    # Construct a SQL `SELECT * FROM posts WHERE id = post_id` statement.
    # =========================================================================
     
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()

    # Guard Clause: Short-circuit with 404 if post does not exist in database.
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


    # STEP 2: FOREIGN KEY / RELATIONSHIP VALIDATION
    # Optimization: Only validate user existence if ownership (`user_id`) is changing.
    # =========================================================================
    if post_data.user_id != post.user_id:
        result= db.execute(select(models.User).where(models.User.id == post_data.user_id))
        user= result.scalars().first()

        # Guard Clause: Prevent foreign key constraint violation by ensuring parent user exists.
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # =========================================================================
    # STEP 3: IN-MEMORY STATE UPDATE
    # Update properties on the tracked ORM model instance (staged in memory session).
    # =========================================================================
    post.title= post_data.title
    post.content= post_data.content
    post.user_id= post_data.user_id


    db.commit()
    db.refresh(post)
    return post
    


# post update patch means partial change
@app.patch("/api/posts/{post_id}", response_model=PostResponse)
def update_post_Partial(
    post_id: int, 
    post_data: PostUpdate,
    db: Annotated[Session, Depends(get_db)]):

   
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()

    # Guard Clause: Short-circuit with 404 if post does not exist in database.
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    

    # since we have set default value none in schema so if data comes value will be set to none but  exclude_unset will only get value that has value so only that change
    update_data = post_data.model_dump(exclude_unset=True)

    # model dump will gave us dict so we fo for loop

    for field, value in update_data.items():
        # setattr dynamically set itel for post object by title like post.title and post.value
        setattr(post, field,value)


    db.commit()
    db.refresh(post)
    return post


# post delete route

@app.delete("/api/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT) # 204 staus mean we are not returning any response just delting the post
def delete_post(post_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    # Guard Clause: Short-circuit with 404 if post does not exist in database.
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    db.delete(post)
    db.commit()





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




