from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, EmailStr


# since we have made user table in database insted of author name string in dummy data we need these schemas
class UserBase(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    email: EmailStr = Field(max_length=120)  # emailStr auto check type email


class UserCreate(UserBase):
    password: str= Field(min_length=8)


class UserPublic(BaseModel):
    # we use configdict in pydatic 2 because in pytin we read data in dict like post["title"]
    # but when we read data from data base we use post.title
    # so here we  are turning from_attributes true so that it can read dot notation also
    model_config = ConfigDict(from_attributes=True)

    id: int
    username:str
    image_file: str | None
    image_path: str  # this is not a column of table but a property if se see in model as a function
    # from attributes= true also has advanatge as it allows to read property

class UserPrivate(UserPublic):
    email: EmailStr

# user update schema


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=1, max_length=50)
    email: EmailStr | None = Field(
        default=None, max_length=120
    )  # emailStr auto check type email
    image_file: str | None = Field(default=None, min_length=1, max_length=200)

class Token(BaseModel):
    access_token: str
    token_type: str 


class PostBase(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)
    # author:str = Field(min_length=1, max_length=100)   commnetd because noe this comes from user as a relationship


class PostCreate(PostBase):
    user_id: int  # TEMPORARTY


# what response we get from api  so this schema is for
# response which have some attributes from postbase and it own attribute id and date_posted


class PostResponse(PostBase):

    # we use configdict in pydatic 2 because in pytin we read data in dict like post["title"]
    # but when we read data from data base we use post.title
    # so here we  are turning from_attributes true so that it can read dot notation also
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    date_posted: datetime  # date time is also seralized for ISO 8601 format so no need for conversions Standard we
    author: UserPublic # pytdenatoc will see author field for its author it validated the user object aginst userresponese and add user data in our api reponse so we get the user json also


class PostUpdate(BaseModel):
    # default=None mean field can either be empty
    title: str | None = Field(default=None, min_length=1, max_length=100)
    content: str | None = Field(default=None, min_length=1)
