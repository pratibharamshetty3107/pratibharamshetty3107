import glob
import json
import os
from pypdf import PdfReader
from common import CHUNKS_FILE, DOCS_DIR

CHUNK_WORDS = 150   # words per chunk
OVERLAP_WORDS = 30  # words shared with the previous chunk

# Every PDF in docs/ -- drop a new file there and re-run.
PDF_PATHS = sorted(glob.glob(os.path.join(DOCS_DIR, "*.pdf")))

chunks = []
for pdf_path in PDF_PATHS:
    text = " ".join(page.extract_text() or "" for page in PdfReader(pdf_path).pages)
    words = text.split()
    step = CHUNK_WORDS - OVERLAP_WORDS
    for i, start in enumerate(range(0, max(len(words) - OVERLAP_WORDS, 1), step)):
        chunks.append({
            "source": os.path.basename(pdf_path),
            "chunk_index": i,
            "content": " ".join(words[start:start + CHUNK_WORDS]),
        })
    print(f"{os.path.basename(pdf_path)}: {len(words)} words")

with open(CHUNKS_FILE, "w", encoding="utf-8") as f:
    json.dump(chunks, f, indent=2, ensure_ascii=False)
print(f"Saved {len(chunks)} chunks to {CHUNKS_FILE}")
