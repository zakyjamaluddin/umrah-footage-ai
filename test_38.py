from app.database import get_setting
from google import genai

key = get_setting("gemini_api_key")
client = genai.Client(api_key=key)

for m in ["gemini-3.8-flash", "gemini-flash-latest"]:
    try:
        res = client.models.generate_content(
            model=m,
            contents="Tes prompt satu kata: halo"
        )
        print(f"MODEL {m}: SUCCESS! Output: {res.text.strip()}")
        break
    except Exception as e:
        print(f"MODEL {m}: ERROR -> {e}")
