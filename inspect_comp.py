import httpx
from composio import Composio

key = "ck_k6bQTJhTGMVmhYpTy1lO"

try:
    c = Composio(api_key=key)
    print("Default headers of composio client:", getattr(c._client, "default_headers", None))
    print("Base url of composio client:", getattr(c._client, "base_url", None))
except Exception as e:
    print("Error:", e)
