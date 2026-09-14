from google import genai
from google.genai import types

client = genai.Client(vertexai=True,project="gcai-sep-26",location="us-central1")
user_prompt = input("Enter your prompt: ")

config = types.GenerateContentConfig(
    tools=[types.Tool(google_search=types.GoogleSearch())]
)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=user_prompt,
    config=config
)

print("Model response is =======", response)