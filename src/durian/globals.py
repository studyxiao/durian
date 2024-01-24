from contextvars import ContextVar
from typing import Any, cast

from werkzeug.wrappers import Request


class Proxy:
    """ContextVar Proxy, similar to werkzeg.local.LocalProxy.

    But only proxies `obj.x` and `str(obj)` methods,
    thus when calling `proxy.x` is the same as dynamically calling `contextvar.get().x`.
    """

    def __init__(self, cv: ContextVar[Request]) -> None:
        self._cv = cv

    def __getattribute__(self, __name: str):
        obj = object.__getattribute__(self, "_cv").get()
        if hasattr(obj, __name):
            return getattr(obj, __name)
        return object.__getattribute__(self, __name)

    def __str__(self) -> str:
        return str(self.cv)

    def __instancecheck__(self, __instance: Any) -> bool:
        return isinstance(__instance, self.cv.get())

    def __subclasscheck__(self, __subclass: type) -> bool:
        return issubclass(__subclass, self.cv.get())


# worker-local (a thread or a coroutine) variable
cv_request: ContextVar[Request] = ContextVar("request")

# alias of _cv_request.get(). `cast()` used to remove type error hint.
request: Request = cast(Request, Proxy(cv_request))
