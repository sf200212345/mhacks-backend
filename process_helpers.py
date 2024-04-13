from google_api import *


def handle_first_message(request_body, connection) -> str:
    '''
        This method should add to message_thread, product_description, and product_factor tables.
        The message will be put into the database at the next step of the function that called this
    '''
    if request_body.get("user_id") is None or not isinstance(request_body.get("user_id"), int):
        return "user_id is missing or not a number"
    user_id = request_body.get("user_id")
    
    if request_body.get("user_message") is None or request_body.get("user_message") == "":
        return "user_message is missing"
    user_message = request_body.get("user_message")


    classification = classify_user_message(user_message)

    if classification == "none":
        return "User's message does not contain a product description"
    elif classification == "other":
        return "User's message contains a product description that is not a tech product"

    # get the user's product description
    product_description = parse_product_description(user_message)

    # create product_description entry and message thread entry
    cursor = connection.execute("INSERT INTO product_description (product_description) VALUES (?)", (product_description,))
    product_description_id = cursor.lastrowid
    cursor = connection.execute("INSERT INTO message_thread (user_id, product_description_id) VALUES (?, ?)", (user_id, product_description_id))

    # now ask for existing factors
    existing_factors = parse_existing_factors(user_message)
    

    # now ask for remaining factors to reach 6 total
    remaining_factors = parse_remaining_factors(user_message, existing_factors)

    # add factors to db
    for factor_name, user_input in [*existing_factors, *remaining_factors]:
        if len(user_input) > 0:
            connection.execute("INSERT INTO product_factor (product_description_id, user_input, factor_name) VALUES (?, ?, ?)",
                                (product_description_id, user_input, factor_name,))
        else:
            connection.execute("INSERT INTO product_factor (product_description_id, factor_name) VALUES (?, ?)",
                                (product_description_id, factor_name,))


def handle_message_generic(request_body, connection):
    '''
        This function needs to return a response and response code
    '''
    pass