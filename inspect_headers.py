from composio import Composio
import httpx

key = "ck_k6bQTJhTGMVmhYpTy1lO"
c = Composio(api_key=key)

# Let's inspect _auth_headers
if hasattr(c._client, "auth_headers"):
    print("auth_headers:", c._client.auth_headers)
elif hasattr(c._client, "_auth_headers"):
    print("_auth_headers:", c._client._auth_headers)

# Let's see all attributes on c._client
print("client attrs:", [a for a in dir(c._client) if not a.startswith("__")])

# Try direct httpx with x-api-key to the actual path requested:
# In composio_client/resources/connected_accounts.py:
# it requested "get" to "/api/v1/connectedAccounts"
for path in ["/api/v1/connectedAccounts", "/api/v1/client/auth/check", "/api/v2/connectedAccounts", "/api/v3/connectedAccounts"]:
    res = httpx.get(f"https://backend.composio.dev{path}", headers={"x-api-key": key})
    print(f"Path: {path} -> {res.status_code}: {res.text[:80]}")
