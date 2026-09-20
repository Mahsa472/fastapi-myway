'''
We need engine to create a new db connection.
sqlalchemy includes sqlite. small and convinient.
'''
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# to make sure the data is always in the same place
BASE_DIR = Path(__file__).resolve().parent # this resolve the place of database.py file and not main.py
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# some facts
# engine = the connection to the DB
# session = one unit of work (one request's worth of reads/writes) over that connection
# SessionLocal = the factory that produces those sessions. You configure the factory once, then spawn a session per request.
DATABASE_URL = f"sqlite:///{DATA_DIR/'blog.db'}"
engine = create_engine(
    DATABASE_URL,
    echo=True,
    connect_args={"check_same_thread": False} # only for sqlite
)

# Base is the infrastucture and it is tied to the engine.
class Base(DeclarativeBase):
    pass

#every request creates a session 
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# create the session from sessionLocal for the request
def get_db():
    with SessionLocal() as session:
        yield session