import flask
import flask_cors
from google_api import *


app = flask.Flask(__name__)
flask_cors.CORS(app)

# add all api routes here
app.add_url_rule("/test-google", view_func=test_google, methods=["GET"])


@app.route("/")
def main():
    return flask.jsonify({"message": "you have reached the root of the backend :)"}), 200
