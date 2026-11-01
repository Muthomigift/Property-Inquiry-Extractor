# Property Inquiry Extractor

A Python script that turns a raw WhatsApp property inquiry into clean, structured data, using the Google Gemini API.

A property agent in Nairobi gets messages like:

> "I am looking for a 3-bedroom house in Kileleshwa, budget around 80k per month"

and currently copies the details into a spreadsheet by hand. This script reads the message, extracts five fields as JSON, converts the JSON into a Python dictionary, and prints each field.

## What it extracts, and why each field matters

| Field | Type | What it holds | Why it matters |
|---|---|---|---|
| `property_type` | text | house, apartment, bedsitter, maisonette | Decides which listings can match. A bedsitter and a maisonette are different products with very different prices, so the agent filters on this first. |
| `bedrooms` | whole number | number of bedrooms | Shows the size the client needs, usually based on household size, and narrows the search. Bedsitters have no bedroom count, so it can be empty. |
| `location` | text | area or neighbourhood | In Nairobi, rent and demand change a lot between neighbourhoods, and clients choose areas for security, schools and travel time. It is the main search filter. |
| `budget_kes` | whole number | budget in Kenya shillings | The client's limit. It is stored as a plain number (80000, not "80k") so a spreadsheet can sort and filter it. |
| `rental_or_sale` | "rental" or "sale" | what the client wants | Rentals and sales are separate listings with different price scales (monthly rent versus purchase price) and different paperwork. Mixing them would make the budget meaningless. |

When a detail is missing from a message, the field is `null` and the script prints `Not stated`. The agent can then see at a glance what to ask the client next.

## How it works

1. **Reads your key.** `GEMINI_API_KEY` is loaded from the `.env` file. The script stops with a clear message if it is missing.
2. **Sends the message with a structured system prompt.** The prompt tells the model to return only a JSON object with the five keys, and sets the rules:
   - `80k` becomes `80000`, and `35M` becomes `35000000`.
   - A monthly budget, or the words "rent" or "to let", means `rental`. The words "buy" or "purchase" mean `sale`. Bedsitters are treated as rentals.
   - If the budget is a range, the higher number is used.
   - If a detail is missing, use `null` and never guess.
   - Messages can mix English and Swahili.
3. **Asks for JSON.** The request sets `response_mime_type` to `application/json` and `temperature` to 0, so the answer is JSON and stays consistent between runs.
4. **Parses the JSON.** The text between the first `{` and the last `}` is converted into a Python dictionary with `json.loads`.
5. **Checks the result.** `check()` confirms that all five fields exist, that `bedrooms` and `budget_kes` are whole numbers or `null`, and that `rental_or_sale` is `rental`, `sale`, or `null`.
6. **Prints each field.** `show()` prints one field per line, with the budget formatted as `KES 80,000` and missing values shown as `Not stated`.

## Setup

1. Install Python 3.9 or newer.
2. Install the libraries:
   ```
   pip install -r requirements.txt
   ```
3. Get a free API key from [Google AI Studio](https://aistudio.google.com).
4. Copy `.env.example` to `.env` and put your key in it:
   ```
   GEMINI_API_KEY=your-key-here
   ```
   Do not use quotes or spaces around `=`.

## Run it

```
python extract_inquiry.py
```

The script first runs five test messages, then asks you to paste your own inquiries. Press Enter on an empty line to stop.

## Test messages and what a correct run extracts

| Message | property_type | bedrooms | location | budget_kes | rental_or_sale |
|---|---|---|---|---|---|
| I am looking for a 3-bedroom house in Kileleshwa, budget around 80k per month | house | 3 | Kileleshwa | 80,000 | rental |
| Do you have any bedsitters near Westlands under 20k? | bedsitter | Not stated | Westlands | 20,000 | rental |
| Hi, I want to buy a 4 bedroom maisonette in Karen, up to 35M | maisonette | 4 | Karen | 35,000,000 | sale |
| Nahitaji 2 bedroom apartment Kilimani, 60k kwa mwezi | apartment | 2 | Kilimani | 60,000 | rental |
| Hello, are there any houses available? | house | Not stated | Not stated | Not stated | Not stated |

The last message is the missing-information test. The table shows what a correct run should produce, and the model's exact wording can differ slightly, for example `Westlands` or `westlands`.

## Error handling

| Problem | What the script does |
|---|---|
| Model busy (503) | Retries 3 times (waits 2, 4, then 8 seconds), then tries the next model |
| Too many requests (429) | Tells you to wait and try again |
| Wrong or missing key (400, 401, 403) | Tells you to check your `.env` file |
| No internet | Tells you to check your connection |
| Answer is not valid JSON, or fields are missing | Prints what went wrong and skips that message |

## Changing the model

The `MODELS` list near the top of `extract_inquiry.py` sets which models are used, in order. Model names change over time. If you see a "model not found" error, copy a current model name from Google AI Studio and update the list.

## Notes

- The free tier has rate limits, and they can change. Check your limits in Google AI Studio.
- On the free tier, the content you send can be used to improve Google's products. Remove names, phone numbers and other personal details before you paste a message.
- The AI can make mistakes, so check important results before you rely on them.
- Never share your API key or upload your `.env` file.

## Files

- `extract_inquiry.py`: the script.
- `requirements.txt`: the libraries to install.
- `.env.example`: a template for your `.env` file.
- `.gitignore`: keeps `.env` out of Git.
- `README.md`: this file.