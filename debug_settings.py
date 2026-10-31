import sqlite3
import traceback
from composio import Composio

conn = sqlite3.connect("data/metadata.db")
c = conn.cursor()
settings = dict(c.execute("SELECT key, value FROM app_settings").fetchall())

print("=== CURRENT DATABASE SETTINGS ===")
for k, v in settings.items():
    preview = v[:6] + "..." + v[-4:] if len(v) > 10 else v
    print(f"Key: {k} (len={len(v)}) -> {preview}")

comp_key = settings.get("composio_api_key")
print("\n=== TESTING COMPOSIO WITH KEY ===")
try:
    client = Composio(api_key=comp_key)
    print("Composio client initialized.")
    accounts = client.connected_accounts.list()
    print("Found accounts:", len(accounts.items))
    for a in accounts.items:
        print(" -> App:", a.app_name, "Status:", a.status, "ID:", a.id)
        
    folder_id = settings.get("google_drive_folder_id")
    print(f"\nTesting search in folder {folder_id}...")
    res = client.actions.execute(action="GOOGLEDRIVE_FIND_FILE", params={"query": f"'{folder_id}' in parents and trashed = false"})
    print("Result type:", type(res))
    print("Result:", str(res)[:300])
except Exception as e:
    print("Composio test failed with error:")
    traceback.print_exc()
