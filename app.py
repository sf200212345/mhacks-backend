import flask
import flask_cors
import sqlite3
import pathlib
import os
import google.generativeai as genai
from process_helpers import *


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
print("GOOGLE_API_KEY:", GOOGLE_API_KEY)


app = flask.Flask(__name__)
flask_cors.CORS(app)


@app.route("/")
def main():
    connection = get_db()
    cursor = connection.execute(
        "SELECT * FROM user WHERE username = ?", ("AI",)
    )
    user = cursor.fetchone()

    return flask.jsonify(**user), 200


@app.route("/test-google/", methods=["GET"])
def test_google():
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content("Say something crazy")
    return flask.jsonify({"message": response.text}), 200


@app.route("/process-user-message/", methods=["POST"])
def process_user_message():
    '''
        This endpoint will take in a user's message and process it accordingly.
        If the user's message is the first in a thread, do the following:
            1. Use gemini 1.0 to parse the message for the product description and any product factors the user has specified
            2. Use gemini to generate any remaining product factors for a total of 6
            3. Store the product description and product factors in the database
            4. Create a message thread for the message and store both the thread and message in the database
        For all incoming messages:
            0. Parse the product factor from the incoming message
            1. Store the message in the database with the incoming message thread
            2. If there is a product_factor_id on the incoming payload, store the product factor in the database
            3. If the user has not reached 6 product factors in the current message thread,
            use gemini 1.0 to generate a prompt for the user for one of the factors that have not gotten user input yet
            4. If the user has reached 6 product factors, send back a boolean flag move_to_compare to indicate that the user can now compare products
            5. Start async task to generate real products from the user's description and product factors, then generate values/ratings/descriptions for each product's factors
    '''
    request_body = flask.request.get_json()
    if request_body is None:
        return flask.jsonify({"message": "Request body is empty"}), 400
    

    if request_body.get("message_thread_id") is None:
        # first message in the thread
        error = handle_first_message(request_body)
        if error:
            return flask.jsonify({"message": error}), 400
    
    # normal handling for messages
    return handle_message_generic(request_body)


@app.route("/get-compare-list/", methods=["POST"])
def get_compare_list():
    '''
        This endpoint will take in either a user's list of product ids that they want to compare,
        or a user's message thread id that they want to compare the products from.
        For each product id, return all the generated product factors/generated ratings for the product as a dictionary
    '''
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
