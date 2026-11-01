import json
import os
import time
import httpx
from dotenv import load_dotenv
from google import genai
from google.genai import errors

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise SystemExit("No API key found. Add GEMINI_API_KEY=your-key to your .env file.")

client = genai.Client(api_key=api_key)

# If the first model is busy, the script tries the next one.
MODELS = ["gemini-3.5-flash", "gemini-3.5-flash-lite"]

FIELDS = ["property_type", "bedrooms", "location", "budget_kes", "rental_or_sale"]

SYSTEM_PROMPT = """You extract details from property inquiry messages sent to a property agent in Nairobi.
Return ONLY a JSON object with exactly these keys:
- property_type: lowercase text, for example "house", "apartment", "bedsitter", "maisonette"
- bedrooms: whole number
- location: text, the area or neighbourhood
- budget_kes: whole number in Kenya shillings (convert "80k" to 80000 and "35M" to 35000000)
- rental_or_sale: "rental" or "sale"

Rules:
- A monthly budget or the words "rent" or "to let" mean "rental". The words "buy" or "purchase" mean "sale". Bedsitters are rental units.
- If the budget is a range, use the higher number.
- If a detail is not in the message, use null. Never guess.
- Messages may mix English and Swahili.
Do not write anything except the JSON."""

TEST_MESSAGES = [
    "I am looking for a 3-bedroom house in Kileleshwa, budget around 80k per month",
    "Do you have any bedsitters near Westlands under 20k?",
    "Hi, I want to buy a 4 bedroom maisonette in Karen, up to 35M",
    "Nahitaji 2 bedroom apartment Kilimani, 60k kwa mwezi",
    "Hello, are there any houses available?",
]


def ask(message):
    # Tries each model up to 3 times when it is busy (error 503).
    for model in MODELS:
        for attempt in range(3):
            try:
                return client.models.generate_content(
                    model=model,
                    contents=message,
                    config={
                        "system_instruction": SYSTEM_PROMPT,
                        "response_mime_type": "application/json",
                        "temperature": 0,
                    },
                )
            except errors.APIError as error:
                if error.code != 503:
                    raise
                wait = 2 ** (attempt + 1)
                print(f"{model} is busy. Retrying in {wait} seconds...")
                time.sleep(wait)
    return None


def check(data):
    # Returns a list of problems found in the extracted data.
    problems = [f"missing field: {field}" for field in FIELDS if field not in data]
    if problems:
        return problems
    if data["bedrooms"] is not None and not isinstance(data["bedrooms"], int):
        problems.append("bedrooms must be a whole number")
    if data["budget_kes"] is not None and not isinstance(data["budget_kes"], int):
        problems.append("budget_kes must be a whole number")
    if data["rental_or_sale"] not in ("rental", "sale", None):
        problems.append("rental_or_sale must be 'rental' or 'sale'")
    return problems


def extract(message):
    try:
        response = ask(message)
    except httpx.RequestError:
        print("No internet connection. Check your connection and try again.")
        return None
    except errors.APIError as error:
        if error.code == 429:
            print("Too many requests or daily limit reached. Wait a minute and try again.")
        elif error.code in (400, 401, 403):
            print("The request was rejected. Check your API key in the .env file.")
        else:
            print("The API returned an error:", error.code)
        return None

    if response is None:
        print("The models are busy right now. Please try again in a few minutes.")
        return None

    text = response.text or ""
    start, end = text.find("{"), text.rfind("}") + 1

    try:
        data = json.loads(text[start:end])
    except json.JSONDecodeError:
        print("Could not read the answer as JSON:", text)
        return None

    problems = check(data)
    if problems:
        print("The answer has problems:", ", ".join(problems))
        return None
    return data


def show(data):
    for field in FIELDS:
        value = data[field]
        if value is None:
            value = "Not stated"
        elif field == "budget_kes":
            value = f"KES {value:,}"
        print(f"  {field}: {value}")


for message in TEST_MESSAGES:
    print(f"Inquiry: {message}")
    data = extract(message)
    if data:
        show(data)
    print()

while True:
    message = input("Paste a new inquiry (or press Enter to stop): ").strip()
    if not message:
        break
    data = extract(message)
    if data:
        show(data)
    print()