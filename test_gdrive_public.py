import httpx
import re
import json

folder_id = "1mq7szK_dg24foLrNxaUfwPLKVO4JO55z"
url = f"https://drive.google.com/drive/folders/{folder_id}"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

r = httpx.get(url, headers=headers, follow_redirects=True)
print("Status code:", r.status_code)
print("Page length:", len(r.text))

# Search for filenames or drive file IDs in the page
# Typically Drive pages embed JSON data like window._DRIVE_rawItemData or similar
found_items = []
patterns = [
    r'(\b[a-zA-Z0-9_-]{28,35}\b)',
]

# Let's search for typical video/image extensions in the text
exts = [".mp4", ".mov", ".jpg", ".jpeg", ".png"]
for ext in exts:
    for match in re.finditer(re.escape(ext), r.text, re.IGNORECASE):
        start = max(0, match.start() - 60)
        end = min(len(r.text), match.end() + 60)
        snippet = r.text[start:end]
        print(f"Found {ext} context: {snippet}")
