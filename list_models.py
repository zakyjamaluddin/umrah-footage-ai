from app.database import get_setting
from google import genai

gem_key = get_setting("gemini_api_key")
client = genai.Client(api_key=gem_key)

print("Listing supported models for generateContent:")
for m in client.models.list():
    methods = getattr(m, "supported_generation_methods", []) or getattr(m, "supported_actions", [])
    name = getattr(m, "name", "")
    if "flash" in name:
        print(f"Model: {name}, Methods: {methods}")
