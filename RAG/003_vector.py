
import time
from itertools import combinations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from sklearn.decomposition import TruncatedSVD


# -------------------------------------------------------------------
# Step 1: Connect to Vertex AI using local credentials (ADC).
# -------------------------------------------------------------------
PROJECT_ID = "gcai-sep-26"
LOCATION = "us-central1"

client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION,
)

# Alternative: Gemini API with API key
# client = genai.Client(api_key="your_api_key_here")


# -------------------------------------------------------------------
# Step 2: Pick a mix of related + unrelated words so the angles
# tell a clear story.
# -------------------------------------------------------------------
words_by_category = {
    "Fruit":   ["apple","applle"],
    "Veichle": ["car"],
    # "Royalty": ["king", "queen"],
}

words = [w for ws in words_by_category.values() for w in ws]
categories = [cat for cat, ws in words_by_category.items() for _ in ws]


# -------------------------------------------------------------------
# Step 3: Generate embeddings (with retry on quota errors).
# -------------------------------------------------------------------
def embed_with_retry(text: str, max_retries: int = 5) -> list[float]:
    delay = 10
    for _ in range(max_retries):
        try:
            result = client.models.embed_content(
                model="gemini-embedding-001",
                contents=text,
                # task_type tells the model what the embedding is FOR.
                # SEMANTIC_SIMILARITY = "I'm going to compare two pieces of
                # text and want a score for how similar they are."
                # Without this, single words land in a narrow cone of the
                # vector space and scores all compress to ~50-55° (useless).
                config=types.EmbedContentConfig(
                    task_type="SEMANTIC_SIMILARITY",
                ),
            )
            return result.embeddings[0].values
        except genai_errors.ClientError as e:
            if e.code == 429:
                print(f"  Quota exceeded. Sleeping {delay}s before retry...")
                time.sleep(delay)
                delay *= 2
            else:
                raise
    raise RuntimeError(f"Failed to embed '{text}' after {max_retries} retries")


print("Generating embeddings...")
vectors = []
for word in words:
    vectors.append(embed_with_retry(word))
    print(f"  '{word}' done")


# -------------------------------------------------------------------
# Step 4: Cosine similarity and angle between two vectors.
# -------------------------------------------------------------------
def cosine_similarity(vec_a, vec_b) -> float:
    """cos(θ) = (A · B) / (|A| * |B|)"""
    a = np.array(vec_a)
    b = np.array(vec_b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def angle_in_degrees(vec_a, vec_b) -> float:
    """The actual angle between the two arrows."""
    cos_theta = cosine_similarity(vec_a, vec_b)
    cos_theta = np.clip(cos_theta, -1.0, 1.0)  # safe vs tiny float drift
    return float(np.degrees(np.arccos(cos_theta)))


# -------------------------------------------------------------------
# Step 5: Print the angle and similarity score for every pair.
# Sorted so the SMALLEST angles (most similar pairs) appear first.
# -------------------------------------------------------------------
print("\n" + "=" * 70)
print("Pairs sorted by angle (smaller angle = more similar meaning):")
print("=" * 70)
print(f"  {'word A':>10}  {'word B':<10}   angle      cos(θ)")
print(f"  {'-'*10}  {'-'*10}   -------    ------")

pairs = []
for i, j in combinations(range(len(words)), 2):
    angle = angle_in_degrees(vectors[i], vectors[j])
    sim = cosine_similarity(vectors[i], vectors[j])
    pairs.append((words[i], words[j], angle, sim))

pairs.sort(key=lambda p: p[2])  # smallest angle first
for word_a, word_b, angle, sim in pairs:
    print(f"  {word_a:>10}  {word_b:<10}   {angle:6.2f}°    {sim:+.4f}")


# -------------------------------------------------------------------
# Step 6: Reduce 3072 dims -> 3 with TruncatedSVD, then draw arrows.
#
# Why TruncatedSVD and not PCA?
#   PCA subtracts the MEAN of all vectors before reducing. With only
#   2 vectors that forces them to point in opposite directions (180°)
#   after centering -- destroying the very angle we want to show.
#   TruncatedSVD skips centering, so the angle-from-origin is kept.
# -------------------------------------------------------------------
n_components = min(3, len(vectors))
svd = TruncatedSVD(n_components=n_components)
reduced = svd.fit_transform(vectors)

if reduced.shape[1] < 3:
    padding = np.zeros((reduced.shape[0], 3 - reduced.shape[1]))
    vectors_3d = np.hstack([reduced, padding])
else:
    vectors_3d = reduced

df = pd.DataFrame({
    "x": vectors_3d[:, 0],
    "y": vectors_3d[:, 1],
    "z": vectors_3d[:, 2],
    "word": words,
    "category": categories,
})

fig = px.scatter_3d(
    df, x="x", y="y", z="z",
    text="word", color="category",
    title="Cosine Similarity = Angle Between Arrows",
)
fig.update_traces(marker=dict(size=8), textposition="top center")

# Draw arrow (line + cone) from origin to each word.
for _, row in df.iterrows():
    fig.add_trace(go.Scatter3d(
        x=[0, row["x"]], y=[0, row["y"]], z=[0, row["z"]],
        mode="lines",
        line=dict(color="gray", width=3),
        showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Cone(
        x=[row["x"]], y=[row["y"]], z=[row["z"]],
        u=[row["x"]], v=[row["y"]], w=[row["z"]],
        sizemode="absolute", sizeref=0.15, anchor="tip",
        showscale=False,
        colorscale=[[0, "gray"], [1, "gray"]],
        hoverinfo="skip",
    ))


# -------------------------------------------------------------------
# Step 7: Draw a small ARC + angle label between each pair of arrows
# (computed on the 3D projection so it matches what's drawn).
# -------------------------------------------------------------------
def slerp_arc(vec_a, vec_b, radius, n_points=30):
    """Curved path from one direction to another at a fixed radius."""
    a = np.array(vec_a, dtype=float)
    b = np.array(vec_b, dtype=float)
    a_unit = a / np.linalg.norm(a)
    b_unit = b / np.linalg.norm(b)
    cos_t = np.clip(np.dot(a_unit, b_unit), -1.0, 1.0)
    theta = np.arccos(cos_t)
    if theta < 1e-6:
        return np.tile(a_unit * radius, (n_points, 1))
    sin_t = np.sin(theta)
    ts = np.linspace(0, 1, n_points)
    arc = np.array([
        (np.sin((1 - t) * theta) / sin_t) * a_unit
        + (np.sin(t * theta) / sin_t) * b_unit
        for t in ts
    ])
    return arc * radius


# Use a small radius so arcs sit near the origin, not over the words.
arc_radius = np.linalg.norm(vectors_3d, axis=1).mean() * 0.35

for i, j in combinations(range(len(words)), 2):
    # 3D angle (matches the visible arrows). Real semantic angle is in terminal.
    a3 = vectors_3d[i]
    b3 = vectors_3d[j]
    cos_t = np.clip(
        np.dot(a3, b3) / (np.linalg.norm(a3) * np.linalg.norm(b3)),
        -1.0, 1.0,
    )
    angle_3d = float(np.degrees(np.arccos(cos_t)))

    arc = slerp_arc(a3, b3, radius=arc_radius)

    # The arc curve.
    fig.add_trace(go.Scatter3d(
        x=arc[:, 0], y=arc[:, 1], z=arc[:, 2],
        mode="lines",
        line=dict(color="orange", width=4),
        showlegend=False,
        hoverinfo="skip",
    ))
    # Angle text at the middle of the arc.
    mid = arc[len(arc) // 2]
    fig.add_trace(go.Scatter3d(
        x=[mid[0]], y=[mid[1]], z=[mid[2]],
        mode="text",
        text=[f"{angle_3d:.0f}°"],
        textfont=dict(size=14, color="red"),
        showlegend=False,
        hoverinfo="skip",
    ))

fig.show()

print("\nLook at the plot, then look at the printed angles above.")
print("Arrows pointing the same way have a SMALL angle and HIGH cos(θ).")
print("That's how RAG finds the document closest in meaning to your question.")
