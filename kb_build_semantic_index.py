import os, json, pickle
from kb.loader import load_all, compile_packs

MODEL_NAME = "all-MiniLM-L6-v2"

def main():
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
    except Exception as e:
        print("Please install sentence-transformers: pip install sentence-transformers torch")
        return

    packs = load_all()
    compiled = compile_packs(packs)

    texts, ids = [], []
    for item in compiled:
        title = item.get("title","")
        summary = item.get("summary","")
        pats = " ".join(item.get("patterns",{}).get("include", []))
        txt = f"{title}. {summary}. {pats}"
        texts.append(txt)
        ids.append(item.get("id"))

    model = SentenceTransformer(MODEL_NAME)
    vecs = model.encode(texts, normalize_embeddings=True)
    out = {"model_name": MODEL_NAME, "vectors": vecs, "ids": ids, "texts": texts}

    out_path = os.path.join(os.path.dirname(__file__), "kb", "semantic_index.pkl")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as f:
        pickle.dump(out, f)
    print("✅ Built semantic index:", out_path, "entries:", len(ids))

if __name__ == "__main__":
    main()
