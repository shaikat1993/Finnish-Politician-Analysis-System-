import os
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

# Make sure your OPENAI_API_KEY is set in your environment or .env file
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("[ERROR] OPENAI_API_KEY not set in environment!")
    exit(1)

client = OpenAI(api_key=api_key)

try:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello! What is the capital of Finland?"}]
    )
    print("[SUCCESS] OpenAI API response:")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"[ERROR] OpenAI API call failed: {e}")
