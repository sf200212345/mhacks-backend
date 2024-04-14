import google.generativeai as genai
import os
import time
import json

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

RETRY_INTERVALS = [1, 2, 4, 8, 16, 32]


def classify_user_message(user_message: str) -> str:
    '''
        This function should take in a user message and return the classification of the message
        Classification can be: has tech product, no product, other product
    '''
    prompt = f"""

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

"""
    generated_text = generic_google_request("models/gemini-pro", prompt, response_type="text")
    return generated_text


def parse_existing_factors(user_message: str):
    '''
        Send the user message to gemini and parse the existing factors from the response
    '''
    prompt = f"""

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


def parse_remaining_factors(user_message: str, existing_factors):
    '''
        Send the user message to gemini and parse the remaining factors from the response
    '''
    prompt = f"""

"""
    # this should be an array of strings. Should only generate 6 - len(existing_factors) strings
    generated_array = generic_google_request("models/gemini-pro", prompt, response_type="json")
    output = []
    # make output same as existing factors to make things easy
    for factor_name in generated_array:
        output.append([factor_name, ""])
    return output


def generate_prompt_for_factor(factor_name: str):
    '''
        Send the factor name to gemini and generate a prompt for the user to give input on the factor
    '''
    prompt = f"""

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
    prompt = f"""

"""
    # this should just be an array of strings
    generated_products = generic_google_request("models/gemini-1.5-pro-latest", prompt, response_type="json")
    return generated_products


def generate_real_product_factors_using_product(product_description: str, product_name: str, product_factors):
    '''
        Send the product description, product, and factors to gemini and generate real product values/descriptions
        For only the entered product
    '''
    prompt = f"""

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
    prompt = f"""

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

# change response_mime_type to application/json if you want a json response
def generic_google_request(model_name: str, prompt: str, response_type="text"):
    '''
        This function should be able to take in a model name and prompt, then return the response from the model
        Use this function to make requests to the google api
    '''
    global RETRY_INTERVALS
    for index, interval in enumerate(RETRY_INTERVALS):
        try:
            model = genai.GenerativeModel(
                model_name,
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
