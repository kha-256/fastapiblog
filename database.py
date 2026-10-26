## database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./blog.db"

engine = create_engine(                        #establish connection here
    SQLALCHEMY_DATABASE_URL,                      
    connect_args={"check_same_thread": False},  # since fast api and postgress handle multiple threads unlike sqllite that why we are turning it false
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)    # seesion maker is a libraty for sessions
                                                                               # session is transaction with database and each request has its own session
                                                                               # by turning autocommit and autoflush false mean we want to control when chnages are commited as  standard pattern


class Base(DeclarativeBase):  # parent class for all models, maps Python classes to DB tables
    pass


def get_db():                       # dependency that provides a DB session to each request
    with SessionLocal() as db:      # opens a new session
        yield db                    # passes session to route, then closes it automatically after
                                    # this function auto cleanup if any erroe occur in request