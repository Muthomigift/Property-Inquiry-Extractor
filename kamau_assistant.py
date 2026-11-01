
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("Gemini API key not found. Check your .env file.")

client = genai.Client(api_key=API_KEY)

system_prompt = """
You are a professional customer service assistant
for Kamau Stores, a wholesale distributor in Nairobi.

YOUR RESPONSIBILITIES:
- Answer questions about orders, pricing and delivery only.
- All prices must be in KES. Never mention USD.
- Delivery covers Nairobi, Mombasa, Kisumu and Nakuru only.
- Never invent product prices, stock information or order details.
- If you do not have enough information, ask the customer
  for the missing details.
- If a question is outside your scope, respond:
  "Please call our office on 0712 345 678 for that."

COMMUNICATION RULES:
- Be polite and professional.
- Give clear and helpful answers.
- Understand specific customer questions.
- End every response with:
  "Asante kwa kuwasiliana."
"""

chat = client.chats.create(
    model="gemini-3.8-flash",
    config=types.GenerateContentConfig(
        system_instruction=system_prompt,
        max_output_tokens=512
    )
)

print("       KAMAU STORES ASSISTANT")
print("Welcome! How can we help you today?")

while True:

    question = input("\nAsk any question: ").strip()

    # Check if customer wants to exit
    if question.lower() in ["exit", "quit", "bye"]:
        print("\nThank you for contacting Kamau Stores.")
        print("Asante kwa kuwasiliana.")
        break

    # Prevent empty questions
    if not question:
        print("Please enter a question.")
        continue

    try:
        response = chat.send_message(message=question)

        print("\nKamau Stores Assistant:")
        print(response.text)

    except Exception as e:
        print("\nAn error occurred:", e)
        print("Please try again.")

