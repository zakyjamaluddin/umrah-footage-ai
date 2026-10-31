import traceback
from app.database import get_setting
from google import genai

gem_key = get_setting("gemini_api_key")
print("GEMINI KEY:", gem_key[:6] if gem_key else None)

client = genai.Client(api_key=gem_key)

# Test models generate content
for m in ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.5-flash", "gemini-3.8-flash"]:
    try:
        res = client.models.generate_content(
            model=m,
            contents="Halo, apakah kamu aktif?"
        )
        print(f"Model {m}: SUCCESS -> {res.text.strip()[:40]}")
        break
    except Exception as e:
        print(f"Model {m}: FAILED -> {e}")

# Test embedding model
for emb_model in ["text-embedding-004", "embedding-001"]:
    try:
        res = client.models.embed_content(
            model=emb_model,
            contents="test embedding text",
        )
        print(f"Embedding {emb_model}: SUCCESS -> {len(res.embeddings[0].values)} dims")
        break
    except Exception as e:
        print(f"Embedding {emb_model}: FAILED -> {e}")
