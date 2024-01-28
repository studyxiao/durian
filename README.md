# Durian

Durian is a WSGI API application framework based on werkzeug (similar to Flask).

> This project is intended as a tool for learning the Flask source code, with the goal of gaining a deeper understanding of the inner workings of Flask and implementing a minimal web framework. Flask is an excellent web framework and you should avoid reinventing the wheel. This project is not guaranteed to be maintained.

**Durian includes the following features:**

- URL router (Werkzeug) and router decorator
- Global request (base on ContextVar)
- APIException and Exception decorator
- JSONResponse only
- Type hinting

**Durian excludes the following features:**

- Custom headers
- Session
- App configuration
- Blueprint
- Class-based views
- Template (jinja2)
- File handling
- Signal
- before/after decorator
- CLI
- Logging

![./docs/images/flow](images/flow.excalidraw.png)

## Requirements

- Python 3.12+
- Werkzeug 3.0.1+

## Example

`example/app.py`

```python
from durian import API, APIException, request

app = API()


@app.route("/")
def index():
    """simple JSON response"""
    return "hello world!"


@app.route("/book/<int:id>", methods=["POST"])
def book(id):
    """url_parser method status_code response_type"""
    return {"id": id}, 201


@app.route("/exception")
def raise_exception():
    raise APIException({"msg": "raise custom exception"}, 400)


@app.route("/json", methods=["POST"])
def handle_json():
    """handle request body and query param"""
    data = request.json or {}
    q = request.args.get("q", "")
    return {**data, "q": q}


@app.errorhandler(404)
def not_found(exception):
    """define custom error handler"""
    return APIException({"msg": "source not found."}, 404)


app.run("127.0.0.1", 8000)

```

Runing the example with `python example/app.py` will give you the following result:

![./docs/images/result](images/result.png)
