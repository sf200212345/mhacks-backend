import google.generativeai as genai
import os
import time


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

RETRY_INTERVALS = [1, 2, 4, 8, 16, 32]


def classify_user_message(user_message: str) -> str:
    '''
        This function should take in a user message and return the classification of the message
        Classification can be: has tech product, no product, other product
    '''
    pass

def parse_product_description(user_message: str) -> str:
    ''''
        Send the user message to gemini and parse the product description from the response
    '''
    pass

def parse_existing_factors(user_message: str):
    '''
        Send the user message to gemini and parse the existing factors from the response
    '''
    pass

def parse_remaining_factors(user_message: str, existing_factors):
    '''
        Send the user message to gemini and parse the remaining factors from the response
    '''
    pass

def parse_product_factor_user_input(user_message: str, product_factor_name):
    '''
        Send the user message to gemini and parse the user input for the product factor
    '''
    pass

def generate_prompt_for_factor(factor_name: str):
    '''
        Send the factor name to gemini and generate a prompt for the user to give input on the factor
    '''
    pass


# change response_mime_type to application/json if you want a json response
def generic_google_request(model_name: str, prompt: str, response_mime_type="text/plain"):
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
                    response_mime_type=response_mime_type,
                ),
            )
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            if index == len(RETRY_INTERVALS) - 1:
                raise e
            time.sleep(interval)
            continue
