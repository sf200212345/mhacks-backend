import flask
import os
import google.generativeai as genai

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
print("GOOGLE_API_KEY:", GOOGLE_API_KEY)


def test_google():
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content("Say something crazy")
    return flask.jsonify({"message": response.text}), 200


def process_user_message():
    pass


def get_compare_list():
    pass