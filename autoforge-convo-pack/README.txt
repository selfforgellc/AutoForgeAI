# AutoForge Conversational Pack (Friendly Shop Tech, Focused Flow)

Drop-in upgrade to add conversational understanding on top of your KB.

## Includes
- main.py — unified conversational backend
- kb/matcher_hybrid.py — rules + semantic + intent-map + system bias
- kb/conversation_state.py — short-term per-session memory
- kb/intents_map.json — slang → intent hints
- kb_build_semantic_index.py — precompute embeddings

## Setup
pip install fastapi uvicorn[standard] pydantic aiofiles orjson
pip install llama-cpp-python
pip install sentence-transformers torch

Optional: build semantic index (faster, better matches)
python kb_build_semantic_index.py

Run:
uvicorn main:app --reload --port 8000
