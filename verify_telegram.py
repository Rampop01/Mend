import json
import ssl
import urllib.request
from pathlib import Path

ctx = ssl.create_default_context(cafile="/etc/ssl/cert.pem") if Path("/etc/ssl/cert.pem").exists() else ssl.create_default_context()
env_path = Path("/Users/a/.gemini/antigravity/scratch/mend/.env")
env_vars = dict(line.split("=", 1) for line in env_path.read_text().splitlines() if "=" in line and not line.startswith("#"))
token = env_vars["TELEGRAM_BOT_TOKEN"].strip()
base_url = f"https://api.telegram.org/bot{token}"

with urllib.request.urlopen(f"{base_url}/getMe", timeout=10, context=ctx) as resp:
    print("getMe:", resp.read().decode())
