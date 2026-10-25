import os
from google import genai
from google.genai import types

# Shared settings for every RAG script. Change project or models here only.
PROJECT_ID = "gcai-sep-26"
EMBED_MODEL = "gemini-embedding-001"
LLM_MODEL = "gemini-3.5-flash"
BQ_TABLE = f"{PROJECT_ID}.rag.pdf_embeddings"

HERE = os.path.dirname(os.path.abspath(__file__))
CHUNKS_FILE = os.path.join(HERE, "chunks.json")
EMBEDDINGS_FILE = os.path.join(HERE, "chunks_with_embeddings.json")
DOCS_DIR = os.path.join(HERE, "docs")

client = genai.Client(vertexai=True, project=PROJECT_ID)


def embed(texts, task_type):
    """task_type: RETRIEVAL_DOCUMENT for chunks, RETRIEVAL_QUERY for questions."""
    result = client.models.embed_content(
        model=EMBED_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(task_type=task_type),
    )
    return [e.values for e in result.embeddings]