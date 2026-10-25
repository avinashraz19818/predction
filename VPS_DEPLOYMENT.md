# 🚀 WinGo VIP AI Prediction System - Deployment & User Guide

Enterprise-grade Color Prediction Telegram Bot with **Real Game Bet Automation & Live Winning Popup Screen Capture** (powered by Playwright), **24/7 or Scheduled Daily VIP Sessions** (IST), **Telegram Premium Animated Emojis**, and Multi-Game Support (WinGo 30s, 1M, 3M, 5M).

---

## ⚡ Option 1: Direct 1-Click Heroku Deployment

Click the button below or open the URL in your browser to deploy instantly on Heroku with 0 hassle:

[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/avinashraz19818/predction)

**Direct Deployment Link:**
```
https://heroku.com/deploy?template=https://github.com/avinashraz19818/predction
```

### Steps on Heroku:
1. Open the deploy link above.
2. Enter your **BOT_TOKEN** (from [@BotFather](https://t.me/BotFather)).
3. Enter your **ADMIN_IDS** (e.g. `8089603563,8015937475`).
4. Keep the pre-configured **MONGO_URI** or provide your own.
5. Click **Deploy app**.
6. Once deployed, go to the **Resources** tab and turn ON the `worker: python main.py` dyno!

---

## 🖥️ Option 2: VPS One-Line Setup (Ubuntu / Debian)

If running on a VPS server (DigitalOcean, AWS, Hetzner, Contabo, etc.), run these commands:

```bash
# 1. Update system & install dependencies
sudo apt update && sudo apt install -y python3 python3-pip python3-venv git

# 2. Clone Repository
git clone https://github.com/avinashraz19818/predction.git
cd predction

# 3. Create Virtual Environment & Install requirements
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
playwright install-deps chromium
playwright install chromium

# 4. Create .env Configuration File
cat << 'EOF' > .env
BOT_TOKEN=8030162642:AAG4Gbe2pyQv8ZreGyw8vTEhKvVKY2Eiugw
ADMIN_IDS=8089603563,8015937475

MONGO_URI=mongodb+srv://avinash:avinash12@cluster0.wnwd1fv.mongodb.net/?appName=Cluster0
MONGO_DB_NAME=maxie1min

DEFAULT_REGISTER_LINK=https://bdgwin7.com/#/register?invitationCode=833131014850
DEFAULT_PROMO_TEXT=🔥 Maintain 3-5 Level Fund for 100% Daily Profit!

OPERATING_MODE=24_7
TIMEZONE=Asia/Kolkata

DEMO_AUTO_BET=true
DEMO_LOGIN_URL=https://bdgwina.biz/#/login
DEMO_USERNAME=6556745550
DEMO_PASSWORD=win1222
EOF

# 5. Start Bot in Background
chmod +x start
./start
```

---

## 🎯 3. Operating Modes: 24/7 vs Scheduled VIP Sessions

You can toggle between modes anytime directly inside the Telegram Bot `/admin` panel with **1 click**:

### Mode A: ⚡ 24/7 Continuous Mode
- Bot runs non-stop 24 hours a day.
- Every single round generates an AI signal, places a real bet, detects the real winning popup, and sends the celebration card + screenshot.

### Mode B: 🕒 Scheduled VIP Sessions (Daily IST)
- Bot runs organized VIP prediction sessions per day:
  - **Session 1 (Morning):** `11:00 AM – 11:30 AM IST`
  - **Session 2 (Afternoon):** `02:00 PM – 02:30 PM IST`
  - **Session 3 (Evening):** `05:00 PM – 05:30 PM IST`
  - **Session 4 (Night VIP):** `08:30 PM – 09:00 PM IST`
- **15-Minute Advance Alert:** At `10:45 AM`, the bot broadcasts:
  > 🚨 *VIP PREDICTION SESSION ALERT! Starting in 15 Minutes at 11:00 AM. Maintain 5-6 Level Funds.*
- **Session Live Kickoff:** At `11:00 AM`, the bot broadcasts:
  > 🟢 *SESSION 1 IS NOW LIVE! Follow strictly with 3X Martingale.*
- **Live Signals & Real Win Screenshots** are posted during the 30-minute session.
- **Session Completion Report:** Automatically wraps up with:
  > 🏆 *SESSION 1 SUMMARY: 15 Rounds | 14 Wins | 93.3% Accuracy | Net Profit: +₹4,500 | Next Session: 02:00 PM IST.*

---

## 🎮 4. Real Win Popup Screenshot (Playwright)

- Unlike simple bots that send text only or fake canvas images, this system uses a **headless mobile Chromium browser (Playwright)**.
- It logs into your game account, selects the period, places the real bet, and uses a fast detector (`80ms` loop) to catch the actual **native "Congratulations" winning popup** on the live game screen.
- The authentic winning popup screenshot is captured and posted directly to your Telegram channel!
- If the browser is temporarily disconnected or re-authenticating, a pixel-perfect backup renderer ensures channel posts never miss.

---

## 📱 5. Telegram Bot Admin Commands

Send `/start` or `/admin` to your bot:
- **⚡ Mode Toggle:** Switch between 24/7 and Scheduled Sessions with 1 click.
- **🕒 Sessions:** View and adjust scheduled session hours.
- **🎮 Playwright Status:** Check live game login status and test bet + screenshot capture directly in chat.
- **📢 Manage Channels:** Add channels, assign WinGo 30s/1m/3m/5m, and customize colored action buttons.
- **📊 System Stats:** Real-time analytics, overall win rates, and streak counters.
