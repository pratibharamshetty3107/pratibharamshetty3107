import json
import sys
from sklearn.metrics.pairwise import cosine_similarity
from common import EMBEDDINGS_FILE, embed

TOP_K = 3

question = sys.argv[1] if len(sys.argv) > 1 else "how i can use corporate cards?"

with open(EMBEDDINGS_FILE, encoding="utf-8") as f:
    chunks = json.load(f)

print(f"Loaded {len(chunks)} chunks with embeddings from {EMBEDDINGS_FILE}")
query_vector = embed([question], "RETRIEVAL_QUERY")[0]
print(f"Question: {question}  ->  {len(query_vector)} dims")
scores = cosine_similarity([query_vector], [c["embedding"] for c in chunks])[0]
print(f"Scores: {len(scores)} scores, min={min(scores):.4f}, max={max(scores):.4f}")
top = sorted(zip(scores, chunks), key=lambda p: p[0], reverse=True)[:TOP_K]

print(f"Question: {question}\n")
for rank, (score, chunk) in enumerate(top, 1):
    print(f"#{rank}  score={score:.4f}  {chunk['source']} chunk {chunk['chunk_index']}")
    print(f"    {chunk['content']}\n")

from google import genai
from google.genai import types

client = genai.Client(vertexai=True,project="gcai-sep-26",location="us-central1")

#user_prompt = input("Enter your prompt: ")


response = client.models.generate_content(
    model="gemini-2.5-pro",
    contents= f" Always use user {question} to answer the question using chunk {top}. If the answer is not in the context, say 'I don't know'.\n\nContext:\n" + top[0][1]['content'] + "\n\nQuestion: " + question,
    config=types.GenerateContentConfig(temperature=0.0),  # minimum = most deterministic, grounded answers
)

print(response.text)


