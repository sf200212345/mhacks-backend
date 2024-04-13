import sqlite3
from google_api import parse_product_description



def handle_first_message(request_body) -> str:
    '''
        This method should add to message_thread, product_description, and product_factors tables.
        The message will be put into the database at the next step of the function that called this
    '''
    if request_body.get("user_id") is None or not isinstance(request_body.get("user_id"), int):
        return "user_id is missing or not a number"
    user_id = request_body.get("user_id")
    
    if request_body.get("user_message") is None or request_body.get("user_message") == "":
        return "user_message is missing"
    user_message = request_body.get("user_message")

    product_description = parse_product_description(user_message)

    # create product_description entry and message thread entry


    # now ask for existing factors


    # add factors to db


    # now ask for remaining factors to reach 6 total


    # add factors to db


def handle_message_generic(request_body):
    '''
        This function needs to return a response and response code
    '''
    pass