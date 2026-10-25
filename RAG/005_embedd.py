import json
from common import CHUNKS_FILE, EMBEDDINGS_FILE, EMBED_MODEL, embed

with open(CHUNKS_FILE, encoding="utf-8") as f:
    chunks = json.load(f)

vectors = embed([c["content"] for c in chunks], "RETRIEVAL_DOCUMENT")
for chunk, vector in zip(chunks, vectors):
    chunk["embedding"] = vector

with open(EMBEDDINGS_FILE, "w", encoding="utf-8") as f:
    json.dump(chunks, f, indent=2, ensure_ascii=False)
print(f"Embedded {len(chunks)} chunks with {EMBED_MODEL} ({len(vectors[0])} dims) -> {EMBEDDINGS_FILE}")
