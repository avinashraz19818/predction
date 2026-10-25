# 👑 WinGo VIP AI Prediction System & Real Bet Auto-Capture

[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/avinashraz19818/predction)

Ek high-speed, enterprise-grade Telegram Bot jo **WinGo 30s, 1 Minute, 3 Minute aur 5 Minute** ke live lottery results track karta hai, AI pattern detection ke sath **BIG / SMALL** aur **Lucky Numbers (0-9)** predict karta hai, Playwright headless browser ke through real game par bet lagata hai aur **Asli In-Game "Congratulations" Winning Popup ka Live Screenshot** capture karke Telegram channels me post karta hai!

---

## 🚀 1-Click Heroku Deployment

Neeche diye gaye link par click karke aap 1-click me Heroku par deploy kar sakte hain:

```
https://heroku.com/deploy?template=https://github.com/avinashraz19818/predction
```

---

## ✨ Key Advanced Features

### 1. 📸 Real Playwright Live Win Popup Screen Capture (smex style)
- Headless Chromium persistent browser session ke sath game me logged in rehta hai.
- Game me real bet lagata hai aur round khatam hone par **actual native "Congratulations" winning popup** (`.winning`, `.winning-body.isWin`, `.WinningTip__C`) ko 80ms fast detector se monitor karta hai.
- Asli game screen ka high-resolution screenshot direct Telegram channel par deliver hota hai!
- Agar browser busy ho ya reconnect ho raha ho, to authentic built-in HD card generator backup provide karta hai taaki koi round miss na ho.

### 2. 🕒 24/7 Mode VS Scheduled Daily VIP Sessions (IST)
Admin panel se 1 click me mode change karein:
- **⚡ 24/7 Mode:** Non-stop lagatar har round ke signals aate hain.
- **🕒 Scheduled VIP Sessions (Daily IST):**
  - **Session 1 (Morning):** `11:00 AM – 11:30 AM IST`
  - **Session 2 (Afternoon):** `02:00 PM – 02:30 PM IST`
  - **Session 3 (Evening):** `05:00 PM – 05:30 PM IST`
  - **Session 4 (Night VIP):** `08:30 PM – 09:00 PM IST`
  - **15-Min Advance Alert:** Session shuru hone se 15 minute pehle wallet fund maintain karne ka alert message channel me jata hai.
  - **Session Live Kickoff:** Session start hote hi live announcement post hoti hai.
  - **Session Wrap-up Summary:** Session complete hone par total rounds, total wins, accuracy %, max streak aur net profit ka attractive report card share hota hai!

### 3. 👑 Telegram Premium Animated Emojis & Sleek VIP UI
- VIP Crown, Golden Trophy, Fire Streak, Animated Target aur Lightning icons.
- Clean Unicode bold typography, uniform progress bars aur separator lines.
- Automatic fallback mechanism taaki bina premium accounts me bhi clean formatting bani rahe.

### 4. 🔘 Native Styled Colored Action Buttons
- Green (Success Style), Red (Danger Style), Blue (Primary Style) buttons:
  - `[ 🟢 REGISTER VIP ACCOUNT 🟢 ]`
  - `[ 🔴 LIVE PROOF CHANNEL 🔴 ]`
  - `[ 🎁 CLAIM VIP BONUS 🎁 ]`

### 5. 🛡️ 3-5 Level Martingale Safe Recovery
- Dynamic level tracking.
- Win hone par automatically Level 1 par reset.

---

## 📁 Project Architecture

```
predction/
├── Procfile               # Heroku worker process definition
├── app.json               # Heroku 1-Click Deploy template
├── runtime.txt            # Python 3.11 runtime
├── requirements.txt       # Dependencies (Playwright, PTB, PyMongo, Pillow, pytz)
├── config.py              # Configuration & Game URLs loader
├── main.py                # Main bot application runner
├── database/
│   └── mongo.py           # MongoDB channel management, sessions & stats
├── engine/
│   └── predictor.py       # AI Trend & Lucky Numbers predictor
├── services/
│   ├── lottery_api.py     # WinGo 30s, 1m, 3m, 5m live data fetcher
│   ├── playwright_worker.py # Playwright Real Bet & Win Popup Capture Engine
│   └── bet_automation.py  # Automation coordination & fallback layer
├── bot/
│   ├── handlers.py        # /admin interactive controls (Mode, Sessions, Browser)
│   ├── keyboards.py       # Styled Channel, Sessions & Admin keyboards
│   ├── templates.py       # VIP cards (Signals, Wins, Alerts, Wrap-up)
│   ├── scheduler.py       # Multi-game & Session controller loop
│   └── card_generator.py  # Pillow HD win card generator
└── start.bat / start      # Windows / Linux startup scripts
```

---

## 🛠️ Quick VPS Setup (Ubuntu / Debian)

```bash
git clone https://github.com/avinashraz19818/predction.git
cd predction
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install-deps chromium
playwright install chromium
chmod +x start
./start
```

---

## 📱 Bot Admin Panel (`/admin`)

Bot ko `/admin` ya `/start` command bhejein:
- **⚡ Toggle Mode:** 24/7 Mode aur Scheduled Sessions ke beech switch karein.
- **🕒 Sessions:** Session timings aur target rounds dekhein.
- **🎮 Browser Status:** Real Playwright live game connection check karein aur live test bet + screenshot execute karein.
- **📢 Channels:** Naye channels add karein, games assign karein (30s, 1M, 3M, 5M) aur colored buttons set karein.
- **📊 System Stats:** Total lifetime predictions, wins, aur accuracy rates dekhein.
