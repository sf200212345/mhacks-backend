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

    all_products = []

    if request_body.get("product_ids") is not None:
        product_ids = request_body.get("product_ids")
        for product_id in product_ids:
            cursor = connection.execute("SELECT * FROM product WHERE id = ?", (product_id,))
            product = cursor.fetchone()
            curr_product = {
                "product_id": product['id'],
                "name": product['product_code'],
            }
            all_products.append(curr_product)
    else:
        cursor = connection.execute("SELECT * FROM product WHERE product_description_id = (SELECT product_description_id FROM message_thread WHERE id = ?)", (message_thread_id,))
        products = cursor.fetchall()

        for product in products:
            curr_product = {
                "product_id": product['id'],
                "name": product['product_code'],
            }
            all_products.append(curr_product)

    output = []
    for product in all_products:
        curr_product_factors = {}
        for factor_name in product_factors.values():
            curr_product_factors[factor_name] = {}
        print(curr_product_factors, "curr_product_factors")

        product_id = product['product_id']

        cursor = connection.execute("SELECT * FROM product_factor_rating WHERE product_id = ?", (product_id,))
        product_factor_ratings = cursor.fetchall()
        print(product_factor_ratings, "product_factor_ratings", product_id)
        for rating in product_factor_ratings:
            curr_factor_name = product_factors[rating['product_factor_id']]
            curr_product_factors[curr_factor_name]["rating"] = rating['generated_rating']
        
        cursor = connection.execute("SELECT * FROM generated_product_factor WHERE product_id = ?", (product_id,))
        generated_product_factors = cursor.fetchall()
        for factor in generated_product_factors:
            curr_factor_name = product_factors[factor['product_factor_id']]
            curr_product_factors[curr_factor_name]["value"] = factor['generated_value']
            curr_product_factors[curr_factor_name]["description"] = factor['generated_description']
        print(curr_product_factors, "curr_product_factors")

        local_output = []
        for name, factor in curr_product_factors.items():
            if not (factor.get("value") is None or factor.get("rating") is None or factor.get("description") is None):
                local_output.append({
                    "attributeName": name,
                    "attributeValue": factor['value'],
                    "attributeRating": factor['rating']
                })

        product["attributes"] = local_output

        output.append(product)
    print(len(output), "output length")
    return flask.jsonify({"products": output}), 200
