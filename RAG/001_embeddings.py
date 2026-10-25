from google import genai

client = genai.Client(vertexai=True,project="gcai-sep-26",location="us-central1")

result = client.models.embed_content(
        model="gemini-embedding-001",
        contents="dog"
)

print(result.embeddings)

# -0.015227566473186016,
#    -0.013213993981480598,