import flask


def get_compare_list_db(request_body, connection):
    '''
        This endpoint will take in either a user's list of product ids that they want to compare,
        or a user's message thread id that they want to compare the products from.
        For each product id, return all the generated product factors/generated ratings for the product as a dictionary
    '''
    message_thread_id = request_body.get("message_thread_id")
    cursor = connection.execute("SELECT * FROM product_factor WHERE product_description_id = (SELECT product_description_id FROM message_thread WHERE id = ?)", (message_thread_id,))
    temp_factors = cursor.fetchall()
    product_factors = {}

    for factor in temp_factors:
        product_factors[factor['id']] = factor['factor_name']

    output = []

    if request_body.get("product_ids") is not None:
        product_ids = request_body.get("product_ids")
        for product_id in product_ids:
            cursor = connection.execute("SELECT * FROM product WHERE id = ?", (product_id,))
            product = cursor.fetchone()
            curr_product = {
                "product_id": product['id'],
                "product_name": product['product_code'],
            }
            for factor_name in product_factors.values():
                curr_product[factor_name] = {}

            cursor = connection.execute("SELECT * FROM product_factor_rating WHERE product_id = ?", (product[0],))
            product_factor_ratings = cursor.fetchall()
            for rating in product_factor_ratings:
                curr_factor_name = product_factors[rating['product_factor_id']]
                curr_product[curr_factor_name]["rating"] = rating['generated_rating']
            
            cursor = connection.execute("SELECT * FROM generated_product_factor WHERE product_id = ?", (product[0],))
            generated_product_factors = cursor.fetchall()
            for factor in generated_product_factors:
                curr_factor_name = product_factors[factor['product_factor_id']]
                curr_product[curr_factor_name]["value"] = factor['generated_value']
                curr_product[curr_factor_name]["description"] = factor['generated_description']

            output.append(curr_product)
    else:
        cursor = connection.execute("SELECT * FROM product WHERE product_description_id = (SELECT product_description_id FROM message_thread WHERE id = ?)", (message_thread_id,))
        products = cursor.fetchall()

        for product in products:
            curr_product = {
                "product_id": product['id'],
                "product_name": product['product_code'],
            }
            for factor_name in product_factors.values():
                curr_product[factor_name] = {}

            cursor = connection.execute("SELECT * FROM product_factor_rating WHERE product_id = ?", (product[0],))
            product_factor_ratings = cursor.fetchall()
            for rating in product_factor_ratings:
                curr_factor_name = product_factors[rating['product_factor_id']]
                curr_product[curr_factor_name]["rating"] = rating['generated_rating']
            
            cursor = connection.execute("SELECT * FROM generated_product_factor WHERE product_id = ?", (product[0],))
            generated_product_factors = cursor.fetchall()
            for factor in generated_product_factors:
                curr_factor_name = product_factors[factor['product_factor_id']]
                curr_product[curr_factor_name]["value"] = factor['generated_value']
                curr_product[curr_factor_name]["description"] = factor['generated_description']

            output.append(curr_product)
    
    return flask.jsonify({"products": output}), 200
