from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def rate_limit_key(request: Request) -> str:
    return request.headers.get("x-user-id") or get_remote_address(request)


limiter = Limiter(key_func=rate_limit_key)

