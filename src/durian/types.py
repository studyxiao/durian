from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from werkzeug.exceptions import HTTPException

if TYPE_CHECKING:
    from durian.wrappers import Response

# Response.body
type ResponseBody = str | bytes | list[Any] | dict[Any, Any]

type ResponseValue = "Response" | ResponseBody
# the return value from a view function: body or tuple(body, status_code)
type ReturnValue = ResponseValue | tuple[ResponseValue, int] | HTTPException

# view function decorator
type RouteCallable = Callable[..., ReturnValue]
type RouteMethod = list[str] | tuple[str] | set[str]

type ErrorCallable = Callable[..., ReturnValue]
