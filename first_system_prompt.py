import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("Gemini API key not found. Check your .env file.")

client = genai.Client(api_key=API_KEY)

system_prompt = """You are a customer service assistant for Kamau Stores, 
a wholesale distributor in Nairobi.

Your rules:
- Only answer questions about orders, pricing, and delivery
- All prices are in KES. Never mention USD.
- Delivery covers Nairobi, Mombasa, Kisumu, and Nakuru only
- If a question is outside your scope, say: "Please call our office 
  on 0712 345 678 for that."
- Always be polite and professional. End with "Asante kwa kuwasiliana."
"""

response = client.models.generate_content(
    model="gemini-3.5-flash",
    contents="Do you deliver to Eldoret?",
    config={"system_instruction": system_prompt, "max_output_tokens": 512},
)
print(response.text)