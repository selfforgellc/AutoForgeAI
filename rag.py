import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from pathlib import Path

# --------------------------------------------------
# Configuration
# --------------------------------------------------

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
KNOWLEDGE_FOLDER = "knowledge"

# --------------------------------------------------
# Load Embedding Model
# --------------------------------------------------

model = SentenceTransformer(EMBEDDING_MODEL_NAME)

# --------------------------------------------------
# Load Knowledge Base
# --------------------------------------------------

knowledge_texts = []
knowledge_paths = []

knowledge_path = Path(KNOWLEDGE_FOLDER)

if knowledge_path.exists():
    for file in knowledge_path.glob("*.txt"):
        with open(file, "r", encoding="utf-8") as f:
            text = f.read()
            knowledge_texts.append(text)
            knowledge_paths.append(file.name)

# --------------------------------------------------
# Build FAISS Index
# --------------------------------------------------

if knowledge_texts:
    embeddings = model.encode(knowledge_texts)
    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings))
else:
    index = None


# --------------------------------------------------
# Retrieve Context Function
# --------------------------------------------------

def retrieve_context(query: str, top_k: int = 3) -> str:
    """
    Returns top relevant knowledge snippets for the query.
    """

    if not index or not knowledge_texts:
        return ""

    query_embedding = model.encode([query])
    distances, indices = index.search(np.array(query_embedding), top_k)

    retrieved_texts = []
    for idx in indices[0]:
        if 0 <= idx < len(knowledge_texts):
            retrieved_texts.append(knowledge_texts[idx])

    return "\n\n".join(retrieved_texts)
