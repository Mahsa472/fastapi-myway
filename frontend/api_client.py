'''
Talks to the backend API over HTTP.
This app never touches the database, it uses the same /api endpoints as any other client.
'''
import httpx


class ApiError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def _error_message(data, status_code: int) -> str:
    # FastAPI sends {"detail": "text"} for HTTPException
    # and {"detail": [{"loc": [...], "msg": "..."}]} for 422 validation errors from pydantic
    detail = data.get("detail") if isinstance(data, dict) else None
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list):
        return "\n".join(f"{error['loc'][-1]}: {error['msg']}" for error in detail)
    return f"Request failed ({status_code})"


class Api:
    def __init__(self, client: httpx.AsyncClient, token: str | None = None):
        self.client = client # one shared client for the whole app, created in main.py
        self.token = token   # the logged-in user's JWT, read from their cookie

    async def _request(self, method: str, path: str, **kwargs):
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        try:
            response = await self.client.request(method, f"/api{path}", headers=headers, **kwargs)
        except httpx.RequestError:
            raise ApiError(503, "The API is not reachable right now. Is the api_app container running?") from None

        if response.status_code == 204:
            return None
        try:
            data = response.json()
        except ValueError:
            data = None
        if response.is_error:
            raise ApiError(response.status_code, _error_message(data, response.status_code))
        return data

    # users
    async def login(self, email: str, password: str) -> str:
        # OAuth2PasswordRequestForm expects form fields and calls the email "username"
        data = await self._request("POST", "/users/token", data={"username": email, "password": password})
        return data["access_token"]

    async def register(self, full_name: str, email: str, password: str):
        return await self._request("POST", "/users", json={"full_name": full_name, "email": email, "password": password})

    async def me(self):
        return await self._request("GET", "/users/me")

    async def get_user(self, user_id: int):
        return await self._request("GET", f"/users/{user_id}")

    async def get_user_posts(self, user_id: int):
        return await self._request("GET", f"/users/{user_id}/posts")

    async def update_user(self, user_id: int, data: dict):
        return await self._request("PATCH", f"/users/{user_id}", json=data)

    async def delete_user(self, user_id: int):
        return await self._request("DELETE", f"/users/{user_id}")

    # posts
    async def list_posts(self):
        return await self._request("GET", "/posts")

    async def get_post(self, post_id: int):
        return await self._request("GET", f"/posts/{post_id}")

    async def create_post(self, title: str, content: str):
        return await self._request("POST", "/posts", json={"title": title, "content": content})

    async def update_post(self, post_id: int, title: str, content: str):
        return await self._request("PUT", f"/posts/{post_id}", json={"title": title, "content": content})

    async def delete_post(self, post_id: int):
        return await self._request("DELETE", f"/posts/{post_id}")
