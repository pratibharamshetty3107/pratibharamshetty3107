from fastmcp import FastMCP
from google import genai
from google.cloud import storage
from google.genai import types
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
import io
import os
from datetime import datetime

mcp = FastMCP("pdf_image_generator")
PROJECT = "gcai-sep-26"
LOCATION = "us-central1" 
IMAGE_MODEL = "gemini-2.5-flash-image"
BUCKET = "tt-fastmcp-demo-002"

client = genai.Client(vertexai=True, project=PROJECT, location=LOCATION)
bucket = storage.Client(project=PROJECT).bucket(BUCKET)

def _upload(name, ext, data, content_type):
    """Upload bytes to GCS and return a browser URL (needs Google sign-in + bucket read access)."""
    # Timestamp + sanitised name: unique, readable object names with no
    # characters that break URLs.
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)[:40] or "file"
    blob = bucket.blob(f"{safe}-{stamp}.{ext}")
    # content_type makes the browser show the PDF/image instead of downloading it.
    blob.upload_from_string(data, content_type=content_type)
    # storage.cloud.google.com = authenticated URL: the bucket stays private, no
    # signed-URL setup needed; access is controlled by bucket IAM.
    return f"https://storage.cloud.google.com/{BUCKET}/{blob.name}"


@mcp.tool
def generate_pdf(title: str, content: str) -> str:
    """Create a PDF with a title and body text. Blank lines separate paragraphs.
    Returns a URL to the PDF."""
    buf = io.BytesIO()
    styles = getSampleStyleSheet()
    story = [Paragraph(title, styles["Title"]), Spacer(1, 12)]
    for para in content.split("\n\n"):
        if para.strip():
            story.append(Paragraph(para.strip().replace("\n", "<br/>"), styles["BodyText"]))
            story.append(Spacer(1, 8))
    SimpleDocTemplate(buf, pagesize=A4).build(story)
    return _upload(title, "pdf", buf.getvalue(), "application/pdf")

@mcp.tool
def create_image(prompt: str, aspect_ratio: str = "1:1") -> str:
    """Generate an image from a text prompt using Gemini image on Vertex AI.
    aspect_ratio: 1:1, 3:4, 4:3, 9:16 or 16:9. Returns a URL to the image."""
    result = client.models.generate_content(
        model=IMAGE_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],  # ask for an image only, no text
            image_config=types.ImageConfig(aspect_ratio=aspect_ratio),
        ),
    )
    # The image arrives as inline bytes in one of the response parts. If safety
    # filters block the prompt there is no image part, so we return a clear
    # message instead of crashing; the agent can relay it to the user.
    parts = result.candidates[0].content.parts if result.candidates else []
    image = next((p.inline_data for p in parts or [] if p.inline_data), None)
    if image is None:
        return "No image returned (prompt may have been blocked by safety filters)."
    # Use the MIME type the model returned (usually PNG) for the file extension.
    mime = image.mime_type or "image/png"
    return _upload(prompt, mime.split("/")[-1], image.data, mime)

if __name__ == "__main__":
    if os.getenv("PORT"):
        mcp.run(transport="http", host="0.0.0.0", port=int(os.environ["PORT"]))
    else:
        mcp.run()
