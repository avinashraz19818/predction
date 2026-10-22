import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

admin_ids_raw = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(x.strip()) for x in admin_ids_raw.split(",") if x.strip().isdigit()]

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "maxie1min")

DEFAULT_REGISTER_LINK = os.getenv("DEFAULT_REGISTER_LINK", "https://bdgwin7.com/#/register")
DEFAULT_PROMO_TEXT = os.getenv("DEFAULT_PROMO_TEXT", "🔥 Maintain 3-5 Level Fund for 100% Daily Profit!")

# Supported WinGo Game Modes
WINGO_GAMES = {
    "wingo_30s": {
        "id": "wingo_30s",
        "name": "WinGo 30s",
        "display_name": "⏱️ WinGo 30 Seconds",
        "duration_sec": 30,
        "api_url": "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"
    },
    "wingo_1m": {
        "id": "wingo_1m",
        "name": "WinGo 1M",
        "display_name": "⏱️ WinGo 1 Minute",
        "duration_sec": 60,
        "api_url": "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
    },
    "wingo_3m": {
        "id": "wingo_3m",
        "name": "WinGo 3M",
        "display_name": "⏱️ WinGo 3 Minutes",
        "duration_sec": 180,
        "api_url": "https://draw.ar-lottery01.com/WinGo/WinGo_3M/GetHistoryIssuePage.json"
    },
    "wingo_5m": {
        "id": "wingo_5m",
        "name": "WinGo 5M",
        "display_name": "⏱️ WinGo 5 Minutes",
        "duration_sec": 300,
        "api_url": "https://draw.ar-lottery01.com/WinGo/WinGo_5M/GetHistoryIssuePage.json"
    }
}

# Demo Account Automation settings (Defaults to user's provided BDGWin demo account)
DEMO_AUTO_BET = os.getenv("DEMO_AUTO_BET", "true").lower() == "true"
DEMO_LOGIN_URL = os.getenv("DEMO_LOGIN_URL", "https://bdgwina.biz/#/login")
DEMO_USERNAME = os.getenv("DEMO_USERNAME", "6556745550")
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "win1222")
