import json

from werkzeug.wrappers import Response as BaseResponse

from durian.types import ResponseBody


class Response(BaseResponse):
    """API Response"""

    body: ResponseBody | None = None
    status_code: int = 200
    default_mimetype: str = "application/json"

    def __init__(
        self,
        body: ResponseBody | None = None,
        status: int | None = None,
    ) -> None:
        if not isinstance(body, (bytes, bytearray)):
            self.body = json.dumps(body)  # parse json
        else:
            # TODO bytes handle
            self.body = body
        super().__init__(self.body, status)


class APIException(Response, Exception):
    """same as Response, can be raise error"""

    body: ResponseBody | None = "Internal Error"
    status_code: int = 500

    def __init__(
        self, body: ResponseBody | None = None, status: int | None = None
    ) -> None:
        self.body = body or self.body
        self.status_code = status or self.status_code
        super().__init__(self.body, self.status_code)
