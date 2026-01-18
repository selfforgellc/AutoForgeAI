import os, faiss, json
from typing import List, Tuple
from pathlib import Path
from sentence_transformers import SentenceTransformer

EMB_MODEL = SentenceTransformer("all-MiniLM-L6-v2")  # local, ~80MB
INDEX_DIR = Path(os.getcwd()) / "kb_index"
INDEX_DIR.mkdir(exist_ok=True)
INDEX_PATH = INDEX_DIR / "faiss.index"
META_PATH  = INDEX_DIR / "meta.jsonl"

def _load_index():
    if INDEX_PATH.exists():
        return faiss.read_index(str(INDEX_PATH))
    return faiss.IndexFlatIP(384)

def add_docs(docs: List[Tuple[str,str]]):
    index = _load_index()
    vecs = EMB_MODEL.encode([t for _,t in docs], normalize_embeddings=True)
    index.add(vecs.astype("float32"))
    with open(META_PATH, "a", encoding="utf-8") as f:
        for (doc_id, text) in docs:
            f.write(json.dumps({"id": doc_id, "text": text})+"\n")
    faiss.write_index(index, str(INDEX_PATH))

def topk(query: str, k=5):
    index = _load_index()
    if index.ntotal == 0:
        return []
    q = EMB_MODEL.encode([query], normalize_embeddings=True).astype("float32")
    D, I = index.search(q, k)
    metas = list(open(META_PATH, "r", encoding="utf-8")) if META_PATH.exists() else []
    out = []
    for idx in I[0]:
        if idx < 0 or idx >= len(metas): continue
        out.append(json.loads(metas[idx]))
    return out
