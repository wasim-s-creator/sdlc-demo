import os
import requests
from pathlib import Path

# ====== HARD-CODED CONFIG ======
BOT_TOKEN = "8399179214:AAGjcSbLquG4eopDhXGByLhREdSfULguYgQ"
CHAT_ID = "-4908287951"

# ====== GET ENV VARIABLES FROM WORKFLOW ======
BRANCH = os.getenv("BRANCH_NAME", "unknown")
SHA = os.getenv("SHORT_SHA", "0000000")

# ====== FIND PDF FILE ======
pdf_file = Path(f"outputs/summary_{BRANCH}_{SHA}.pdf")

if not pdf_file.exists():
    print(f"[WARN] PDF file not found: {pdf_file}")
    exit(0)

# ====== SEND PDF TO TELEGRAM ======
url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
with open(pdf_file, "rb") as f:
    files = {"document": f}
    data = {
        "chat_id": CHAT_ID,
        "caption": f"Auto summary — {BRANCH} @ {SHA}"
    }
    response = requests.post(url, files=files, data=data)

if response.status_code == 200:
    print(f"[INFO] PDF sent successfully to Telegram chat {CHAT_ID}")
else:
    print(f"[ERROR] Failed to send PDF: {response.status_code}")
    print(response.text)
