@app.get(root, response_model=)
def home():

* schema is for api requests, what user can send and what should be in response
* model is how we want the db

for each database we need 3 things:
# engine = the connection to the DB
# session = one unit of work (one request's worth of reads/writes) over that connection
# SessionLocal = the factory that produces those sessions. You configure the factory once, then spawn a session per request.


when we have two tables related we have to define relations in models
for two tables, each get a relation column and one which is on many side get the foreignkey column
Also if we add a nested field in schema part, we should thing about async funcs
Each func which has the class which has a nested field, should be called as selectinload
# author is a nested object and it could be that it is not loaded atm of call
# in sync call it will be loaded in that moment
# in Async session it cannot make moment call therefore it should be loaded at first on the query


Adding routers changes two things: @app will be @router and the path should be changed

moving to authentication:
packages:
# it needs pwd to hash the password pwdlib[argon2] ,
# pyjwt to create webtokens , 
# pydantic-settings for managing configurations it is instead of python env because we will have a central configuration which help us to check types quickly, it fails fast when env variables are missing or wrong format, also it creates secrets in pydantic and make sure we don't print the passwords accidently

schema changes:
# we need password in user create
# change Userpublic inherit from UserBase to base and create UserPrivate
# we need a class for Token

new files:
# config.py which comes from pydantic settings to load app configurations



move to postgres
# only database url changes
create a new postgres container with:
docker run -d --name postgres -p 5432:5432 -e POSTGRES_PASSWORD=secret -e POSTGRES_USER=test_user -e POSTGRES_DB=test_db postgres

url will be: DATABASE_URL=postgresql+psycopg://test_user:secret@localhost:5432/test_db

to rerun the container:
docker start <container name/id>

to run commands inside the postgres image:
docker exec -it <container name/id> <command>

uv run alembic upgrade head
# because we already had the version with create tables, with upgrade head it will creates the table inside postgres