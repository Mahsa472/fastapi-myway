'''
Server-rendered frontend. Every page is built here with Jinja2 and sent to the browser as finished HTML.
The data comes from the backend API (api_client.py), never from the database directly.

Login: the JWT from the API is kept in an httpOnly cookie. The browser sends it back with every
request, but JavaScript can't read it, so an XSS bug couldn't steal it.
'''
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated
from urllib.parse import quote, unquote, urlsplit

import httpx
from fastapi import Depends, FastAPI, Form, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

import filters
from api_client import Api, ApiError
from config import settings

BASE_DIR = Path(__file__).resolve().parent
TOKEN_COOKIE = "access_token"
FLASH_COOKIE = "flash"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # one http client for the whole app, it keeps connections to the api open between requests
    app.state.http = httpx.AsyncClient(base_url=settings.api_url, timeout=10)
    yield
    await app.state.http.aclose()


# docs are turned off, this app serves pages and has no API of its own
app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

templates = Jinja2Templates(directory=BASE_DIR / "templates") # autoescapes {{ }} so user text can't inject HTML
templates.env.filters.update(
    date=filters.date_format,
    timeago=filters.time_ago,
    reading_time=filters.reading_time,
    initials=filters.initials,
    excerpt=filters.excerpt,
)
templates.env.globals.update(site_name=settings.site_name, site_tagline=settings.site_tagline)


@app.middleware("http")
async def security(request: Request, call_next):
    # CSRF protection: browsers send an Origin header with form posts, refuse posts made from another site.
    # The SameSite=Lax cookie already blocks most of these, this is a second layer.
    if request.method == "POST":
        origin = request.headers.get("origin")
        if origin and urlsplit(origin).netloc != request.headers.get("host"):
            return PlainTextResponse("Cross-site form submission blocked", status_code=403)

    response = await call_next(request)

    if getattr(request.state, "clear_token", False): # set when the api rejected the token
        response.delete_cookie(TOKEN_COOKIE)
    # the site has no JavaScript at all, so scripts are simply not allowed
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' data:; form-action 'self'; "
        "frame-ancestors 'none'; base-uri 'self'; object-src 'none'"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    return response


# ---------------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------------

def render(request: Request, template: str, status_code: int = 200, **context):
    # the flash message is set by redirect() and shown once on the next page
    flash = request.cookies.get(FLASH_COOKIE)
    context = {
        "user": getattr(request.state, "user", None),
        "flash": unquote(flash) if flash else None,
        **context,
    }
    response = templates.TemplateResponse(request, template, context, status_code=status_code)
    if flash:
        response.delete_cookie(FLASH_COOKIE)
    return response


def redirect(url: str, flash: str | None = None) -> RedirectResponse:
    # 303 makes the browser follow with a GET, so refreshing the next page doesn't resubmit the form
    response = RedirectResponse(url, status_code=303)
    if flash:
        response.set_cookie(FLASH_COOKIE, quote(flash), max_age=60, httponly=True, samesite="lax")
    return response


def set_token_cookie(response, token: str):
    response.set_cookie(
        TOKEN_COOKIE,
        token,
        max_age=settings.token_max_age_minutes * 60,
        httponly=True,  # not readable from JavaScript
        samesite="lax", # not sent with form posts coming from other sites
        secure=settings.cookie_secure,
    )


def safe_next(url: str | None) -> str:
    # only allow paths on this site, "//evil.com" or "https://evil.com" would be an open redirect
    if url and url.startswith("/") and not url.startswith("//") and "\\" not in url:
        return url
    return "/"


# ---------------------------------------------------------------------------------
# dependencies
# ---------------------------------------------------------------------------------

def get_api(request: Request) -> Api:
    return Api(request.app.state.http, request.cookies.get(TOKEN_COOKIE))

ApiDep = Annotated[Api, Depends(get_api)]


async def get_current_user(request: Request, api: ApiDep) -> dict | None:
    """The logged-in user or None. Asked from the api on every page, so an expired token logs you out."""
    request.state.user = None
    if not api.token:
        return None
    try:
        request.state.user = await api.me()
    except ApiError as e:
        if e.status_code != 401:
            raise
        request.state.clear_token = True # the middleware removes the dead cookie
        api.token = None
    return request.state.user

CurrentUser = Annotated[dict | None, Depends(get_current_user)]


class LoginRequired(Exception):
    pass


async def require_user(user: CurrentUser) -> dict:
    if user is None:
        raise LoginRequired()
    return user

RequiredUser = Annotated[dict, Depends(require_user)]


# ---------------------------------------------------------------------------------
# error handling
# ---------------------------------------------------------------------------------

ERROR_TITLES = {
    400: "That didn't work",
    403: "Not allowed",
    404: "Page not found",
    503: "Service unavailable",
}


@app.exception_handler(LoginRequired)
async def login_required_handler(request: Request, exc: LoginRequired):
    return redirect(f"/login?next={quote(request.url.path)}", flash="Please log in first.")


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    if exc.status_code == 401:
        request.state.clear_token = True
        return redirect(f"/login?next={quote(request.url.path)}", flash="Your session expired, please log in again.")
    return render(
        request, "error.html", status_code=exc.status_code,
        code=exc.status_code,
        title=ERROR_TITLES.get(exc.status_code, "Something went wrong"),
        message=exc.message,
    )


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException):
    # no route dependency ran, so look up the user here to show the right nav links
    try:
        await get_current_user(request, get_api(request))
    except ApiError:
        pass
    message = "There's nothing at this address." if exc.status_code == 404 else exc.detail
    return render(
        request, "error.html", status_code=exc.status_code,
        code=exc.status_code,
        title=ERROR_TITLES.get(exc.status_code, "Something went wrong"),
        message=message,
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    # /posts/abc fails the int check on post_id, for a visitor that's just a page that doesn't exist
    if any(error["loc"][0] == "path" for error in exc.errors()):
        return await http_error_handler(request, StarletteHTTPException(404))
    return await http_error_handler(request, StarletteHTTPException(400, "Some of the form fields were missing or invalid."))


# ---------------------------------------------------------------------------------
# posts
# ---------------------------------------------------------------------------------

@app.get("/")
async def home(request: Request, user: CurrentUser, api: ApiDep):
    posts = await api.list_posts()
    return render(request, "home.html", posts=posts)


@app.get("/posts/new")
async def new_post_page(request: Request, user: RequiredUser):
    return render(request, "post_form.html", heading="Write a new story", submit_label="Publish", post={}, cancel_url="/")


@app.post("/posts/new")
async def create_post(
    request: Request,
    user: RequiredUser,
    api: ApiDep,
    title: Annotated[str, Form()],
    content: Annotated[str, Form()],
):
    try:
        post = await api.create_post(title, content)
    except ApiError as e:
        if e.status_code != 422:
            raise
        # show the form again with what they typed, so nothing is lost
        return render(
            request, "post_form.html", status_code=422,
            heading="Write a new story", submit_label="Publish", cancel_url="/",
            post={"title": title, "content": content}, error=e.message,
        )
    return redirect(f"/posts/{post['id']}", flash="Your story is live.")


@app.get("/posts/{post_id}")
async def post_detail(request: Request, post_id: int, user: CurrentUser, api: ApiDep):
    post = await api.get_post(post_id)
    return render(request, "post.html", post=post)


@app.get("/posts/{post_id}/edit")
async def edit_post_page(request: Request, post_id: int, user: RequiredUser, api: ApiDep):
    post = await api.get_post(post_id)
    if post["user_id"] != user["id"]:
        raise ApiError(403, "You can only edit your own stories.")
    return render(
        request, "post_form.html",
        heading="Edit story", submit_label="Save changes", cancel_url=f"/posts/{post_id}", post=post,
    )


@app.post("/posts/{post_id}/edit")
async def edit_post(
    request: Request,
    post_id: int,
    user: RequiredUser,
    api: ApiDep,
    title: Annotated[str, Form()],
    content: Annotated[str, Form()],
):
    try:
        await api.update_post(post_id, title, content) # the api checks ownership again (403)
    except ApiError as e:
        if e.status_code != 422:
            raise
        return render(
            request, "post_form.html", status_code=422,
            heading="Edit story", submit_label="Save changes", cancel_url=f"/posts/{post_id}",
            post={"id": post_id, "title": title, "content": content}, error=e.message,
        )
    return redirect(f"/posts/{post_id}", flash="Changes saved.")


# deleting needs a confirmation page, because without JavaScript there is no confirm() popup
@app.get("/posts/{post_id}/delete")
async def delete_post_page(request: Request, post_id: int, user: RequiredUser, api: ApiDep):
    post = await api.get_post(post_id)
    if post["user_id"] != user["id"]:
        raise ApiError(403, "You can only delete your own stories.")
    return render(
        request, "confirm.html",
        title="Delete this story?",
        message=f"“{post['title']}” will be permanently deleted. This can't be undone.",
        action=f"/posts/{post_id}/delete",
        confirm_label="Delete story",
        cancel_url=f"/posts/{post_id}",
    )


@app.post("/posts/{post_id}/delete")
async def delete_post(post_id: int, user: RequiredUser, api: ApiDep):
    await api.delete_post(post_id)
    return redirect("/", flash="Story deleted.")


# ---------------------------------------------------------------------------------
# users
# ---------------------------------------------------------------------------------

@app.get("/users/{user_id}")
async def profile(request: Request, user_id: int, user: CurrentUser, api: ApiDep):
    # both requests go out at the same time
    author, posts = await asyncio.gather(api.get_user(user_id), api.get_user_posts(user_id))
    posts.sort(key=lambda post: post["created_date"], reverse=True) # this endpoint returns them unordered
    return render(request, "profile.html", author=author, posts=posts)


@app.get("/account")
async def account_page(request: Request, user: RequiredUser):
    return render(request, "account.html", email=user["email"])


@app.post("/account/email")
async def update_email(request: Request, user: RequiredUser, api: ApiDep, email: Annotated[str, Form()]):
    try:
        await api.update_user(user["id"], {"email": email})
    except ApiError as e:
        if e.status_code not in (409, 422):
            raise
        return render(request, "account.html", status_code=e.status_code, email=email, error=e.message)
    return redirect("/account", flash="Email updated.")


@app.get("/account/delete")
async def delete_account_page(request: Request, user: RequiredUser):
    return render(
        request, "confirm.html",
        title="Delete your account?",
        message="Your account and all of your stories will be permanently deleted. This can't be undone.",
        action="/account/delete",
        confirm_label="Delete my account",
        cancel_url="/account",
    )


@app.post("/account/delete")
async def delete_account(user: RequiredUser, api: ApiDep):
    await api.delete_user(user["id"])
    response = redirect("/", flash="Your account was deleted.")
    response.delete_cookie(TOKEN_COOKIE)
    return response


# ---------------------------------------------------------------------------------
# login / register / logout
# ---------------------------------------------------------------------------------

@app.get("/login")
async def login_page(request: Request, user: CurrentUser, next: str = "/"):
    if user:
        return redirect(safe_next(next))
    return render(request, "login.html", next=safe_next(next))


@app.post("/login")
async def login(
    request: Request,
    api: ApiDep,
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    next: Annotated[str, Form()] = "/",
):
    try:
        token = await api.login(email, password)
    except ApiError as e:
        if e.status_code not in (401, 422):
            raise
        return render(request, "login.html", status_code=e.status_code, error=e.message, email=email, next=safe_next(next))

    me = await Api(api.client, token).me()
    response = redirect(safe_next(next), flash=f"Welcome back, {me['full_name']}!")
    set_token_cookie(response, token)
    return response


@app.get("/register")
async def register_page(request: Request, user: CurrentUser):
    if user:
        return redirect("/")
    return render(request, "register.html")


@app.post("/register")
async def register(
    request: Request,
    api: ApiDep,
    full_name: Annotated[str, Form()],
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    try:
        await api.register(full_name, email, password)
        token = await api.login(email, password) # log straight in after registering
    except ApiError as e:
        if e.status_code not in (409, 422):
            raise
        return render(
            request, "register.html", status_code=e.status_code,
            error=e.message, full_name=full_name, email=email,
        )
    response = redirect("/", flash=f"Welcome, {full_name}! Your account is ready.")
    set_token_cookie(response, token)
    return response


@app.post("/logout")
async def logout():
    response = redirect("/", flash="You're logged out. See you soon!")
    response.delete_cookie(TOKEN_COOKIE)
    return response
