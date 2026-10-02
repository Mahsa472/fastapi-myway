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

