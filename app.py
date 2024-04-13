import flask
import flask_cors
from google_api import *


app = flask.Flask(__name__)
flask_cors.CORS(app)

# add all api routes here
app.add_url_rule("/test-google", view_func=test_google, methods=["GET"])
app.add_url_rule("/process-user-message", view_func=process_user_message, methods=["POST"])
app.add_url_rule("/get-compare-list", view_func=get_compare_list, methods=["POST"])


@app.route("/")
def main():
    return flask.jsonify({"message": "you have reached the root of the backend :)"}), 200
