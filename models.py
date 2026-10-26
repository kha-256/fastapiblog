## models.py
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


# why we are making usermodel when we have author as a string?
# becuase posts will be associated with the user account and in future we need autheication like login and user

class User(Base):                   # inherits from Base so SQLAlchemy tracks this as a DB table
    __tablename__ = "users"         # actual table name in the database

    # Mapped[type] = python type hint | mapped_column(...) = actual DB column config
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)          # unique row id, auto-incremented
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)  # max 50 chars, must be unique
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)    # max 120 chars, must be unique
    image_file: Mapped[str | None] = mapped_column(                                 # Mapped[str | None] = can be null we are saving image name insted of full paths
        String(200),
        nullable=True,                                                              # optional field
        default=None,                                                               # defaults to no image
    )

    posts: Mapped[list[Post]] = relationship(back_populates="author")               # one user -> many posts also we eaw usin[Post] before its define below so this version of python allows it called forward refernce
                                                                                    # in mapped we define type that posts are the list and set relationship ship with author so all post of this author
                                                                                    # we will use it like user.post to get all user post

    @property
    def image_path(self) -> str:                                                    # helper to return full image URL
        if self.image_file:
            return f"/media/profile_pics/{self.image_file}"                         #user uploaded image
        return "/static/profile_pics/default.jpg"                                   # if not then this  fallback to default avatar


class Post(Base):                   # each instance = one row in posts table
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)          # unique post id
    title: Mapped[str] = mapped_column(String(100), nullable=False)                 # post title, max 100 chars
    content: Mapped[str] = mapped_column(Text, nullable=False)                      # Text = unlimited length content
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),                                                     # links this post to a user
        nullable=False,
        index=True,                                                                 # indexed for faster queries as we
                                                                                   # indexes make reads faster but writes slightly slower (DB has to update the index on every insert/update). For a user_id column this is always worth it.

    )
    date_posted: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),                                                    #store timszone info
        default=lambda: datetime.now(UTC),                                          # auto-set to current UTC time
    )

    author: Mapped[User] = relationship(back_populates="posts")                     # gives access to the User object link back to user as post.author and help us get user back