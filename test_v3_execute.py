import traceback
from composio import Composio

key = "ck_k6bQTJhTGMVmhYpTy1lO"
folder_id = "1mq7szK_dg24foLrNxaUfwPLKVO4JO55z"

c = Composio(api_key=key)

try:
    print(f"Executing GOOGLEDRIVE_FIND_FILE for folder {folder_id}...")
    query = f"'{folder_id}' in parents and trashed = false"
    res = c.tools.execute(
        slug="GOOGLEDRIVE_FIND_FILE",
        arguments={"query": query}
    )
    print("SUCCESS! Result type:", type(res))
    print("Result data:", getattr(res, "data", res))
except Exception as e:
    print("Execution failed:")
    traceback.print_exc()
