## database.py imports (async)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./blog.db"

engine =  create_async_engine(                        #establish connection here
    SQLALCHEMY_DATABASE_URL,                      
    connect_args={"check_same_thread": False},  # since fast api and postgress handle multiple threads unlike sqllite that why we are turning it false
)

AsyncSessionLocal = async_sessionmaker(                           # session maker is a libraty for sessions
    engine,                                                            # session is transaction with database and each request has its own session
    class_=AsyncSession,
    expire_on_commit=False    # recommended for async as it deal will deal with expired object on commit
)    
                                                                                       
                                                                               

class Base(DeclarativeBase):  # parent class for all models, maps Python classes to DB tables
    pass


async def get_db():                       # dependency that provides a DB session to each request
    async with AsyncSessionLocal() as session:      # opens a new session
        yield session                    # passes session to route, then closes it automatically after
                                    # this function auto cleanup if any erroe occur in request