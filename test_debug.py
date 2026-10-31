import os
import traceback
from app.database import get_all_settings
from composio import Composio

settings = get_all_settings()
comp_key = settings.get("composio_api_key")
folder_id = settings.get("google_drive_folder_id")

try:
    c = Composio(api_key=comp_key)
    print("SUCCESS: Composio client created!")
    
    # List connected accounts
    accounts = c.connected_accounts.list()
    print("Found connected accounts count:", len(accounts.items))
    for a in accounts.items:
        print(" -> App Name:", getattr(a, "app_name", None), "Status:", getattr(a, "status", None), "ID:", getattr(a, "id", None))

    # Test tools / action execution
    print("\nTesting execute action GOOGLEDRIVE_FIND_FILE...")
    query = f"'{folder_id}' in parents and trashed = false"
    # In Composio v0.30+, how are actions called?
    print("c attributes:", [x for x in dir(c) if not x.startswith("_")])
    if hasattr(c, "actions"):
        print("c.actions attributes:", [x for x in dir(c.actions) if not x.startswith("_")])
        res = c.actions.execute(action="GOOGLEDRIVE_FIND_FILE", params={"query": query})
        print("Action execute result:", res)
    elif hasattr(c, "tools"):
        print("c.tools attributes:", [x for x in dir(c.tools) if not x.startswith("_")])
except Exception as e:
    traceback.print_exc()
