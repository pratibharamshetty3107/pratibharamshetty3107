from google import genai

client = genai.Client(vertexai=True,project="gcai-sep-26",location="us-central1")

user_prompt = input("Enter your prompt: ")


response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=user_prompt,
    
)

print(response.text)


