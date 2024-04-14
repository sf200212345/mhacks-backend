import google.generativeai as genai
import os
import time
import json

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

RETRY_INTERVALS = [1, 2, 4, 8, 16, 32]


def change_factors_into_string(factors):
    if len(factors) == 0:
        return "No factors specified."
    if factors[0].get('id') is not None:
        return "\n".join([f'factor_name = {factor["factor_name"]}, user_input = {factor["user_input"]}, id = {factor["id"]}' for factor in factors])
    return "\n".join([f'factor_name = {factor["factor_name"]}, user_input = {factor["user_input"]}' for factor in factors])

def classify_user_message(user_message: str) -> str:
    '''
        This function should take in a user message and return the classification of the message
        Classification can be: has tech product, no product, other product
    '''
    prompt = f"""
Here is the user's latest message:
```
{user_message}
```
Please classify the message as one of the following:
1. has tech product (if the user's message contains a request for a tech product recommendation)
2. no product (if the user's message does not contain a request for a tech product recommendation)
3. other product (if the user's message contains a request for a product that is not a tech product)
Output only one of ["has tech product", "no product", "other product"]. Do not output anything else.
"""
    generated_text = generic_google_request("models/gemini-pro", prompt, response_type="text")
    if "no" in generated_text.lower():
        return "none"
    elif "other" in generated_text.lower():
        return "other"
    return "has"


def parse_product_description(user_message: str) -> str:
    ''''
        Send the user message to gemini and parse the product description from the response
    '''
    prompt = f"""
Here is the user's latest message:
```
{user_message}
```
This message contains a request for a tech product recommendation.
Please extract what product the user wants a recommendation for from the message. Output this product and nothing else.
"""
    generated_text = generic_google_request("models/gemini-pro", prompt, response_type="text")
    return generated_text


def parse_existing_factors(user_message: str, product_description: str):
    '''
        Send the user message to gemini and parse the existing factors from the response
    '''
    prompt = f"""
Here is the user's latest message:
```
{user_message}
```
This message contains a request for a recommendation for {product_description}.
Please extract any factors the user wants to consider from their message.
Examples of such factors are: price, speed, color, etc. Do not be limited to these options only.
Output an array of objects with the keys "factor_name" and "user_input".
The "factor_name" should be the name of the factor and "user_input" should be the user's input for that factor.
If the user did not specify an input for a factor, the "user_input" should be an empty string.
Output only this array of objects and nothing else in JSON output format.
"""
    # this should be an array of objects with factor_name and user_input keys
    # user input should have an empty string if no user input was found by the model
    generated_array = generic_google_request("models/gemini-pro", prompt, response_type="json")
    output = []
    for item in generated_array:
        factor_name = item.get("factor_name")
        user_input = item.get("user_input")
        if user_input is None:
            user_input = ""
        output.append([factor_name, user_input])
    return output


def parse_remaining_factors(user_message: str, existing_factors, product_description: str):
    '''
        Send the user message to gemini and parse the remaining factors from the response
    '''
    existing_factors_str = change_factors_into_string(existing_factors)
    prompt = f"""
Here is the user's latest message:
```
{user_message}
```
This message contains a request for a recommendation for {product_description}.
The user has already specified the following {len(existing_factors)} factors:
```
{existing_factors_str}
```
I want to generate {6 - len(existing_factors)} more factors for the user to consider for this product.
Examples of such factors are: price, speed, color, etc. Do not be limited to these options only.
Output an array of strings with the names of the factors the user wants to consider.
Output only this array of strings and nothing else in JSON output format.
"""
    # this should be an array of strings. Should only generate 6 - len(existing_factors) strings
    generated_array = generic_google_request("models/gemini-pro", prompt, response_type="json")
    output = []
    # make output same as existing factors to make things easy
    for factor_name in generated_array:
        output.append([factor_name, ""])
    return output


def generate_prompt_for_factor(factor_name: str, product_description: str):
    '''
        Send the factor name to gemini and generate a prompt for the user to give input on the factor
    '''
    prompt = f"""
The user is asking for a recommendation for {product_description}.
Here is a factor that the user wants to consider: {factor_name}.
Please generate a prompt for the user to give input on this factor, as well as an array of possible values for this factor.
As an example, if the factor is "color", the prompt could be "What color would you like the {product_description} to be?" and the possible values could be ["red", "blue", "green", "black", "white"].
Output an object with the keys "generated_prompt" and "possible_values", where "generated_prompt" is the prompt for the user and "possible_values" is the array of strings for the possible values.
Output only this object and nothing else in JSON output format.
"""
    # force two keys to be defined: generated_prompt and possible_values corresponding to possible values for the factor_name
    generated_dict = generic_google_request("models/gemini-pro", prompt, response_type="json")
    if generated_dict.get("generated_prompt") is None:
        generated_dict["generated_prompt"] = "Sorry, we weren't able to generate a prompt for this factor."
    if generated_dict.get("possible_values") is None or not isinstance(generated_dict.get("possible_values"), list):
        generated_dict["generated_prompt"] += "Sorry, we weren't able to generate possible values for this factor."
        generated_dict["possible_values"] = ["Next factor"]
    return generated_dict


def generate_real_products_using_ai(product_description: str, product_factors):
    '''
        Send the product description and factors to gemini and generate real products
    '''
    product_factors_str = change_factors_into_string(product_factors)
    prompt = f"""
The user is asking for a recommendation for {product_description}.
The user has specified the following factors and user inputs for these factors:
```
{product_factors_str}
```
Please generate a list of exactly 5 real tech products that match the user's description and factors for this product.
This should be a list of strings. Output only this list of strings and nothing else in JSON output format.
"""
    # this should just be an array of strings
    generated_products = generic_google_request("models/gemini-1.5-pro-latest", prompt, response_type="json")
    return generated_products


def generate_real_product_factors_using_product(product_description: str, product_name: str, product_factors):
    '''
        Send the product description, product, and factors to gemini and generate real product values/descriptions
        For only the entered product
    '''
    product_factors_str = change_factors_into_string(product_factors)
    prompt = f"""
The user is asking for a recommendation for {product_description}.
The user has specified the following factors and user inputs for these factors:
```
{product_factors_str}
```
The user is currently consider the product {product_name}.
For each factor specified above, generate what that factor's value would be for this current product.
Also, generate a description for what each product's value means and justify why this product has this value for this factor.
This should be output as an array of objects with the keys "value", "description", and "id", where "value" is the value of the factor, "description" is the description of the value, and "id" is the id of the factor from above.
Output only this array of objects and nothing else in JSON output format.
"""
    # tell the model to put the ids in product_factors into the output as well
    # this should be an array of objects with value, description and id as keys
    generated_factors = generic_google_request("models/gemini-pro", prompt, response_type="json")
    return generated_factors


def generate_real_product_factor_ratings_using_product(product_description, product_name, product_factors):
    '''
        Send the product description, product, and factors to gemini and generate real product ratings
        For only the entered product
    '''
    product_factors_str = change_factors_into_string(product_factors)
    prompt = f"""
The user is asking for a recommendation for {product_description}.
The user has specified the following factors and user inputs for these factors:
```
{product_factors_str}
```
The user is currently consider the product {product_name}.
For each factor specified above, generate a rating between 50 and 100 for that factor for this current product.
This rating should reflect how well this product meets the user's input for this factor and should be as specific of a number as possible.
This should be output as an array of objects with the keys "rating" and "id", where "rating" is the rating of the factor and "id" is the id of the factor from above.
Output only this array of objects and nothing else in JSON output format.
"""
    # tell the model to put the ids in product_factors into the output as well
    # this should be an array of objects with rating and id as keys
    generated_ratings = generic_google_request("models/gemini-pro", prompt, response_type="json")
    return generated_ratings


def clean_generated_text(text: str) -> str:
    return text.strip("\n\t\r`\'\" ")

def text_to_json(text: str):
    '''
        This function should take in a text response from the google api and convert it to a json response
    '''
    cleaned_text = text.replace("\n", "").replace("\r", "").replace("\t", "").replace('`', '').strip("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%^&*()_+-=|;':,.<>?/\\\"~`")
    try:
        output = json.loads(cleaned_text)
    except json.JSONDecodeError:
        print(f"Failed to convert text to json: {cleaned_text}")
        return "", False
    
    return output, True

def generic_google_request(model_name: str, prompt: str, response_type="text"):
    output = generic_google_request_call(model_name, prompt, response_type)
    print(f"Output for prompt: {prompt} is: {output}")
    return output

def generic_google_request_call(model_name: str, prompt: str, response_type="text"):
    '''
        This function should be able to take in a model name and prompt, then return the response from the model
        Use this function to make requests to the google api
    '''
    global RETRY_INTERVALS
    system_instruction = "You are recommending users real tech products based on their input. You will be given a user's message and you will need to generate exactly what the prompt asks of you. The user will likely be a tech noice, so don't use overly technical terms."
    for index, interval in enumerate(RETRY_INTERVALS):
        try:
            model = genai.GenerativeModel(
                model_name,
                system_instruction=system_instruction,
                generation_config=genai.GenerationConfig(
                    temperature=1.0,
                ),
            )
            response = model.generate_content(prompt)
            if response_type == "json":
                output, success = text_to_json(response.text)
                if success:
                    return output
                # otherwise try generating again using for loop
            else:
                return clean_generated_text(response.text)
        except Exception as e:
            print(f"Failed on attempt {index + 1} with error: {e}")
            if index == len(RETRY_INTERVALS) - 1:
                raise e
            time.sleep(interval)
            continue
