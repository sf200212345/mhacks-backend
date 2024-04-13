import google.generativeai as genai
import sqlite3
import os

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)


def parse_product_description(user_message: str) -> str:
    pass