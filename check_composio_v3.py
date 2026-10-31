import httpx
from composio_client import ComposioClient

key = "ck_k6bQTJhTGMVmhYpTy1lO"
client = ComposioClient(api_key=key)
print("Base URL:", client.base_url)

headers = {
    "x-api-key": key,
    "Authorization": f"Bearer {key}"
}

endpoints = [
    "https://api.composio.dev/v1/connectedAccounts",
    "https://api.composio.dev/v1/client/auth/check",
    "https://backend.composio.dev/api/v3/client/auth/check",
    "https://backend.composio.dev/api/v3/connectedAccounts",
    "https://api.composio.dev/v3/connectedAccounts",
    f"{client.base_url}connected_accounts",
    f"{client.base_url}connectedAccounts",
]

for url in endpoints:
    try:
        r = httpx.get(url, headers={"x-api-key": key}, timeout=5.0)
        print(f"URL: {url} -> Status: {r.status_code}, Body: {r.text[:100]}")
    except Exception as e:
        print(f"URL: {url} -> Error: {e}")
