from collections import defaultdict
from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING, ClassVar

from werkzeug import Request, run_simple
from werkzeug.exceptions import HTTPException, default_exceptions
from werkzeug.routing import Map, Rule

from durian.globals import cv_request
from durian.types import ErrorCallable, ReturnValue, RouteCallable, RouteMethod
from durian.wrappers import APIException, Response

if TYPE_CHECKING:
    from _typeshed.wsgi import StartResponse, WSGIEnvironment


class API:
    """WSGI API application framework based on werkzeug (similar to Flask)."""

    # Step 3.1 register routes
    routes: Map = Map()
    # Bind a path and a view function
    view_funcs: ClassVar[dict[str, RouteCallable]] = {}

    exception_handler: ClassVar[dict[int | None, dict[type[Exception], ErrorCallable]]] = defaultdict(dict)

    def route(self, path: str, methods: RouteMethod | None = None) -> Callable[[RouteCallable], RouteCallable]:
        """Decorate a view function for register a route

        Args:
            path (str): url string
            methods (RouteMethod | None, optional): allow reqeust methods. Defaults to ("GET",).
        """

        # Step 3.2
        def decorator(func: RouteCallable) -> RouteCallable:
            self.add_route(path, func, methods)
            return func

        return decorator

    def add_route(
        self,
        path: str,
        func: RouteCallable,
        methods: RouteMethod | None,
    ):
        """Bind a path and a view function as a Rule and register to the route

        Args:
            path (str): url string
            func (RouteCallable): view function
            methods (RouteMethod | None): allow request methods
        """
        endpoint = func.__name__
        assert endpoint not in self.view_funcs, "route already exists."

        if methods is None:
            methods = ("GET",)  # werkzeug auto-add HEAD, OPTIONS
        methods = {item.upper() for item in methods}
        self.routes.add(Rule(path, endpoint=endpoint, methods=methods))
        self.view_funcs[endpoint] = func

    def errorhandler(self, exc_class_or_code: type[Exception] | int) -> Callable[[ErrorCallable], ErrorCallable]:
        """Register a function to handle errors by code or exception class.

        Args:
            exc_class_or_code (type[Exception] | int): HTTP status code or Exception class
        """

        def decorator(func: ErrorCallable) -> ErrorCallable:
            exc_class, code = self._get_exc_class_and_code(exc_class_or_code)
            self.exception_handler[code][exc_class] = func
            return func

        return decorator

    def handle_user_exception(self, exception: Exception) -> ReturnValue:
        """Handle user exception.

        When not APIException occurs, it will query whether
        the corresponding processing function is registered,
        and if so, return the function result.

        Args:
            exception (Exception): not APIException
        """
        exc_class, code = self._get_exc_class_and_code(type(exception))
        code_handler = self.exception_handler.get(code, None)
        if code_handler:
            handler = code_handler.get(exc_class, None)
            if handler:
                return handler(exception)
        raise exception

    def _get_exc_class_and_code(
        self,
        exc_class_or_code: type[Exception] | int,
    ) -> tuple[type[Exception], int | None]:
        """Get exception class and code by exception class or code

        Args:
            exc_class_or_code (type[Exception] | int): HTTP status code or Exception class

        Raises:
            ValueError: not a recognized HTTP error code
            TypeError: not a Exception class
        """
        code: int | None = None
        exc_class: type[Exception] | None = None

        if isinstance(exc_class_or_code, int):
            exc_class = default_exceptions.get(exc_class_or_code)
            if exc_class is None:
                raise ValueError(f"{exc_class_or_code} is not a recognized HTTP error code.")
        else:
            exc_class = exc_class_or_code
        if isinstance(exc_class, Exception):
            raise TypeError(f"{exc_class!r} is a instance not a Exception class.")
        if not issubclass(exc_class, Exception):  # type: ignore
            raise TypeError(f"'{exc_class.__name__}' is not a subclass of Exception.")
        if isinstance(exc_class_or_code, APIException):
            code = exc_class_or_code.status_code
        elif isinstance(exc_class_or_code, HTTPException):
            code = exc_class_or_code.code
        return exc_class, code

    def dispatch_request(self) -> Response:
        """Dispatches the request as well as HTTP exception catching and  error handling

        Returns:
            WSGIApplication: an instance of :class:`~werkzeug.wrappers.Response`
        """
        adapter = self.routes.bind_to_environ(cv_request.get())
        # step 4.
        try:
            rule, values = adapter.match(return_rule=True)
            rv = self.view_funcs[rule.endpoint](**values)
        except APIException as e:
            rv = e
        except HTTPException as e:
            try:
                rv = self.handle_user_exception(e)
            except Exception:
                rv = APIException(e.description, status=e.code)
        except Exception as e:
            # pass errors to the caller for handling
            rv = self.handle_user_exception(e)
        response = self.make_response(rv)
        return response

    def make_response(self, rv: ReturnValue) -> Response:
        """Convert the return value from a view function to an instance of Response.

        Args:
            rv (ReturnValue): the return value from the view function.
            The following types are allowed:

            ``str`` ``bytes``  ``list``  ``dict``

            :class:`~werkzeug.wrappers.Response`

        Raises:
            TypeError: Invalid type of return value from a view function

        Returns:
            Response: an instance of :class:`~werkzeug.wrappers.Response`
        """
        status = None
        if isinstance(rv, tuple):
            if len(rv) == 2 and isinstance(rv[1], int):  # type: ignore
                rv, status = rv
            else:
                raise TypeError("Invalid type of return value from a view function")

        if not isinstance(rv, Response):
            if isinstance(rv, HTTPException):
                rv = APIException(rv.description, status=rv.code or status)
            elif isinstance(rv, str | list | tuple | dict | bytes | bytearray):  # type: ignore
                rv = Response(
                    rv,
                    status=status,
                )
            else:
                raise TypeError("Invalid type of return value from a view function")
        if status is not None:
            rv.status_code = status
        return rv

    def __call__(
        self,
        environ: "WSGIEnvironment",
        start_response: "StartResponse",
    ) -> Iterable[bytes]:
        """The WSGI application called by the WSGI server."""
        # Step 1. create WSGI applicaiton
        return self.wsgi_app(environ, start_response)

    def wsgi_app(
        self,
        environ: "WSGIEnvironment",
        start_response: "StartResponse",
    ) -> Iterable[bytes]:
        """The actual WSGI application."""
        # step 2.
        self.parse_request(environ)
        try:
            try:
                # step 3.
                response = self.dispatch_request()
            except Exception as e:
                # step 5.
                # Errors other than APIException and HTTPException
                response = APIException(body=str(e))
                # raise
            # step 6.
            return response(environ, start_response)
        finally:
            # clean request
            cv_request.reset(self._token)

    def parse_request(self, environ: "WSGIEnvironment"):
        """Parse the request and set the request to global variable.

        Change environ (dict) to Response (class)
        as well as change the request to global variable similar to `flask.reuqest`.
        """
        _request = Request(environ)
        self._token = cv_request.set(_request)

    def run(self, host: str = "127.0.0.1", port: int = 8000):
        """Runs the application on local wsgi serve, which is also a web server.

        Call :func:`werkzeug.serving.run_simple`

        Args:
            host (str, optional): the hostname to listen on. Defaults to "127.0.0.1".
            port (int, optional): the port of the webserver. Defaults to 8000.
        """
        # Step 2. create a server
        run_simple(
            host,
            port,
            self,
            use_reloader=True,
            use_debugger=True,
            threaded=False,
        )
