import typing as t

from werkzeug.exceptions import HTTPException

if t.TYPE_CHECKING:
    from durian.wrappers import Response

# Response.body
ResponseBody: t.TypeAlias = str | bytes | list | dict

ResponseValue: t.TypeAlias = t.Union[
    "Response",
    ResponseBody,
]
# the return value from a view function: body or tuple(body, status_code)
ReturnValue: t.TypeAlias = ResponseValue | tuple[ResponseValue, int] | HTTPException

# view function decorator
RouteCallable: t.TypeAlias = t.Callable[..., ReturnValue]
RouteMethod: t.TypeAlias = list[str] | tuple[str] | set[str]

ErrorCallable = t.Callable[[t.Any], ReturnValue]
