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
