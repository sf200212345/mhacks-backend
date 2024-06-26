from google_api import *
import flask


def handle_first_message(request_body, connection) -> str:
    '''
        This method should add to message_thread, product_description, and product_factor tables.
        The message will be put into the database at the next step of the function that called this
    '''
    if request_body.get("user_id") is None or not isinstance(request_body.get("user_id"), int):
        return "user_id is missing or not a number", -1
    user_id = request_body.get("user_id")
    
    if request_body.get("user_message") is None or request_body.get("user_message") == "":
        return "user_message is missing", -1
    user_message = request_body.get("user_message")


    classification = classify_user_message(user_message)

    if classification == "none":
        return "User's message does not contain a product description", -1
    elif classification == "other":
        return "User's message contains a product description that is not a tech product", -1

    # get the user's product description
    product_description = parse_product_description(user_message)

    # create product_description entry and message thread entry
    cursor = connection.execute("INSERT INTO product_description (product_description) VALUES (?)", (product_description,))
    product_description_id = cursor.lastrowid
    cursor = connection.execute("INSERT INTO message_thread (user_id, product_description_id) VALUES (?, ?)", (user_id, product_description_id))
    message_thread_id = cursor.lastrowid
    

    # now ask for existing factors
    existing_factors = parse_existing_factors(user_message, product_description)

    # now ask for remaining factors to reach 6 total
    remaining_factors = parse_remaining_factors(user_message, existing_factors, product_description)
    num_factors = 0
    # add factors to db
    for factor_name, user_input in [*existing_factors, *remaining_factors]:
        if len(user_input) > 0:
            connection.execute("INSERT INTO product_factor (product_description_id, user_input, factor_name) VALUES (?, ?, ?)",
                                (product_description_id, user_input, factor_name,))
        else:
            connection.execute("INSERT INTO product_factor (product_description_id, factor_name) VALUES (?, ?)",
                                (product_description_id, factor_name,))
        
        num_factors += 1
        # only allow 6 factors per product
        if num_factors >= 6:
            break
    
    return None, message_thread_id


def handle_message_generic(request_body, connection, user_message_parsed: bool):
    '''
        This function needs to return a response and response code
    '''
    if request_body.get("user_id") is None or not isinstance(request_body.get("user_id"), int):
        return flask.jsonify({"message": "user_id is missing or not a number"}), 400
    user_id = request_body.get("user_id")
    
    if request_body.get("user_message") is None or request_body.get("user_message") == "":
        return flask.jsonify({"message": "user_message is missing"}), 400
    user_message = request_body.get("user_message")

    if request_body.get("message_thread_id") is None or not isinstance(request_body.get("message_thread_id"), int):
        return flask.jsonify({"message": "message_thread_id is missing or not a number"}), 400
    message_thread_id = request_body.get("message_thread_id")

    cursor = connection.execute("SELECT * FROM product_description WHERE id = (SELECT product_description_id FROM message_thread WHERE id = ?)", (message_thread_id,))
    product_description_obj = cursor.fetchone()
    product_description = product_description_obj["product_description"]
    product_description_id = product_description_obj["id"]

    # save message to db
    connection.execute("INSERT INTO message (message_thread_id, message_content) VALUES (?, ?)",
                        (message_thread_id, user_message,))
    
    # figure out the user feedback for the current product factor if specified
    if not user_message_parsed:
        if request_body.get("product_factor_id") is not None and not isinstance(request_body.get("product_factor_id"), int):
            return flask.jsonify({"message": "product_factor_id is not a number"}), 400
        product_factor_id = request_body.get("product_factor_id")

        # currently make it so that the user can only input values sent by the backend as the message when we reach this step
        connection.execute("UPDATE product_factor SET user_input = ? WHERE id = ?", (user_message, product_factor_id))
        

    # get all product factors for the current product description
    cursor = connection.execute("SELECT * FROM product_factor WHERE product_description_id = ?", (product_description_id,))
    current_product_factors = cursor.fetchall()

    factor_needs_user_input = None
    for factor in current_product_factors:
        if factor["user_input"] is None or factor["user_input"] == "":
            factor_needs_user_input = factor
            break

    if factor_needs_user_input is not None:
        generated_dict = generate_prompt_for_factor(factor_needs_user_input["factor_name"], product_description)
        connection.execute("INSERT INTO message (message_thread_id, message_content) VALUES (?, ?)",
                            (message_thread_id, generated_dict["generated_prompt"],))
        output_dictionary = {
            "message": generated_dict["generated_prompt"],
            "possible_values": generated_dict["possible_values"] + ["I don't know"],
            "product_factor_id": factor_needs_user_input["id"],
            "message_thread_id": message_thread_id,
        }
        return flask.jsonify(**output_dictionary), 200
    
    generate_real_products(product_description_id, product_description, current_product_factors, connection)
    return flask.jsonify({"move_to_compare": True, "message_thread_id": message_thread_id}), 200


def generate_real_products(product_description_id: int, product_description: str, product_factors, connection):
    '''
        This function should be able to generate real products from the product description and product factors
        It should also generate values/ratings/descriptions for each product's factors
    '''

    real_products = generate_real_products_using_ai(product_description, product_factors)
    for product in real_products:
        product_name = product
        cursor = connection.execute("INSERT INTO product (product_description_id, product_code) VALUES (?, ?)", (product_description_id, product_name))
        product_id = cursor.lastrowid
        

        current_product_factors = generate_real_product_factors_using_product(product_description, product_name, product_factors)
        for factor_obj in current_product_factors:
            connection.execute("INSERT INTO generated_product_factor (product_id, product_factor_id, generated_value, generated_description) VALUES (?, ?, ?, ?)",
                               (product_id, factor_obj["id"], factor_obj["value"], factor_obj["description"]))
        current_factor_ratings = generate_real_product_factor_ratings_using_product(product_description, product_name, product_factors)
        for factor_obj in current_factor_ratings:
            connection.execute("INSERT INTO product_factor_rating (product_id, product_factor_id, generated_rating) VALUES (?, ?, ?)",
                               (product_id, factor_obj["id"], factor_obj["rating"]))
