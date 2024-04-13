import flask
import flask_cors
import sqlite3
import pathlib
import os
import google.generativeai as genai


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
print("GOOGLE_API_KEY:", GOOGLE_API_KEY)


app = flask.Flask(__name__)
flask_cors.CORS(app)


@app.route("/")
def main():
    return flask.jsonify({"message": "you have reached the root of the backend :)"}), 200


@app.route("/test-google", methods=["GET"])
def test_google():
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content("Say something crazy")
    return flask.jsonify({"message": response.text}), 200


@app.route("/process-user-message", methods=["POST"])
def process_user_message():
    pass


@app.route("/get-compare-list", methods=["POST"])
def get_compare_list():
    pass


#------------------------------------------------------------------------------------------
#--------------------------db connection stuff---------------------------------------------
#------------------------------------------------------------------------------------------

# everything below is taken straight from EECS 485
# no need to touch this part
def dict_factory(cursor, row):
    """Convert database row objects to a dictionary keyed on column name.

    This is useful for building dictionaries which are then used to render a
    template.  Note that this would be inefficient for large queries.
    """
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def get_db():
    """Open a new database connection.

    Flask docs:
    https://flask.palletsprojects.com/en/1.0.x/appcontext/#storing-data
    """
    if 'sqlite_db' not in flask.g:
        db_filename = pathlib.Path(__file__).parent / "db.sqlite3"
        flask.g.sqlite_db = sqlite3.connect(str(db_filename))
        flask.g.sqlite_db.row_factory = dict_factory
        # Foreign keys have to be enabled per-connection.  This is an sqlite3
        # backwards compatibility thing.
        flask.g.sqlite_db.execute("PRAGMA foreign_keys = ON")
    return flask.g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Close the database at the end of a request.

    Flask docs:
    https://flask.palletsprojects.com/en/1.0.x/appcontext/#storing-data
    """
    assert error or not error  # Needed to avoid superfluous style error
    sqlite_db = flask.g.pop('sqlite_db', None)
    if sqlite_db is not None:
        sqlite_db.commit()
        sqlite_db.close()
