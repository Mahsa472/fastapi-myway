# FastAPI blog API

A learning project: building a **backend REST API with FastAPI**, step by step, from a single file to an
async, authenticated, containerized service on PostgreSQL.

The backend is the point of this repo. The `frontend/` folder is only a small demo client that uses the API;
it was not the goal.

## What it covers

- **REST API with FastAPI**: routers, path parameters, status codes, `response_model`
- **Pydantic schemas**: separate request and response models (public vs private user data)
- **Async SQLAlchemy 2.0** on **PostgreSQL**, with one-to-many users → posts and cascade delete
- **Alembic** migrations
- **Authentication**: argon2 password hashing, JWT tokens via the OAuth2 password flow
- **Authorization**: a `CurrentUser` dependency, users can only change their own posts and account
- **Config** with `pydantic-settings` and a `.env` file
- **Docker**: multi-stage `Dockerfile` with `uv`, non-root user, and `docker compose` for the API + Postgres

## Stack

Python 3.12 · FastAPI · SQLAlchemy (async) · PostgreSQL 18 · Alembic · Pydantic v2 · PyJWT · pwdlib (argon2) · uv · Docker

## Project layout

```
main.py            creates the app, mounts the routers
routers/users.py   /api/users: register, login, profile, update, delete
routers/posts.py   /api/posts: CRUD with ownership checks
auth.py            password hashing, JWT, CurrentUser dependency
models.py          SQLAlchemy models (User, Post)
schema.py          Pydantic request/response models
database.py        async engine and get_db session dependency
config.py          settings loaded from .env
alembic/           database migrations
frontend/          demo client (separate container, not the focus)
```

## API

| Method | Path | Auth | What it does |
|---|---|---|---|
| POST | `/api/users` | | register |
| POST | `/api/users/token` | | log in, get a JWT |
| GET | `/api/users/me` | ✅ | current user |
| GET | `/api/users/{id}` | | public profile |
| GET | `/api/users/{id}/posts` | | a user's posts |
| PATCH / DELETE | `/api/users/{id}` | owner | update email / delete account |
| GET | `/api/posts` | | all posts, newest first |
| GET | `/api/posts/{id}` | | one post |
| POST | `/api/posts` | ✅ | create a post |
| PUT / PATCH / DELETE | `/api/posts/{id}` | owner | update / delete a post |

Interactive docs: <http://localhost:8080/docs>

## Run it

1. Create a `.env` file next to `docker-compose.yml`:

   ```env
   POSTGRES_USER=bloguser
   POSTGRES_PASSWORD=change-me
   POSTGRES_DB=blog
   SECRET_KEY=a-long-random-string
   # used when running alembic (or the app) from your machine
   DATABASE_URL=postgresql+psycopg://bloguser:change-me@localhost:5432/blog
   ```

2. Start everything:

   ```bash
   docker compose up --build -d
   ```

3. Create the tables (first time only; migrations don't run on startup):

   ```bash
   uv run alembic upgrade head
   ```

Then open the API docs at <http://localhost:8080/docs>, or the demo frontend at <http://localhost:3000>.

## Credits

Built while following [Corey Schafer's FastAPI course](https://github.com/CoreyMSchafer?tab=repositories&q=FastAPI),
