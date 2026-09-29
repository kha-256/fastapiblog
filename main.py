from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()



# dummy data as dict
posts: list[dict] = [
    {
        "id": 1,
        "author": "Corey Schafer",
        "title": "FastAPI is Awesome",
        "content": "This framework is really easy to use and super fast.",
        "date_posted": "April 20, 2025",
    },
    {
        "id": 2,
        "author": "Jane Doe",
        "title": "Python is Great for Web Development",
        "content": "Python is a great language for web development, and FastAPI makes it even better.",
        "date_posted": "April 21, 2025",
    },
]


# #decorator and we are decorating home function with it its base route
# @app.get("/")
# def home():
#   return {"message":"Hello World!!"}

#decorator and we are decorating home function with it its base route but with html response
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
@app.get("/posts", response_class=HTMLResponse, include_in_schema=False)
#if we want same thing on different rout we can do by using multiple decorators so on / and on /post same thing will dsiplay
def home():
  return f"<h1>{posts[0]['title']}</h1>"

#enpoint to get posts and if we search using this  http://127.0.0.1:8000/api/posts we can find it
@app.get("/api/posts")
def get_post():
    return posts