import flask
import flask_cors

app = flask.Flask(__name__)
flask_cors.CORS(app)

@app.route("/")
def main():
    return flask.jsonify({"message": "you have reached the root of the backend :)"}), 200
