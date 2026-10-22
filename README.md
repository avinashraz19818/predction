# 👑 Modern WinGo VIP Prediction Bot (30s, 1M, 3M, 5M)

Ek high-speed, modern aur modular Telegram Bot jo **WinGo 30s, 1 Minute, 3 Minute aur 5 Minute** ke live lottery results track karta hai, AI pattern detection ke sath **BIG / SMALL** aur **Lucky Numbers (0-9)** predict karta hai, BDGWin demo account par auto-bet place karke **Real Winning Screenshots** capture karta hai, aur Telegram channels me alag-alag messages + High-Impact Styled Buttons ke sath send karta hai.

---

## ✨ Features (Kya Naya Hai?)

1. **Real In-Game BDGWin Win Screenshots**:
   - Background headless browser (Selenium + Edge) demo account me login karta hai.
   - Har round me ₹1 ka bet auto-place karta hai.
   - Win aane par **"My history"** tab se official winning record card (Period, Big/Small, Win badge, aur `+₹X.XX` green amount) ka live screenshot lekar Telegram channel me post karta hai!
   - Agar website offline ho ya browser busy ho, to built-in Pillow HD result card auto-generate hota hai taaki koi round miss na ho!

2. **User Account Ki Need Khatam**:
   - Pyrogram / Telethon user session ki zaroorat nahi hai. Poora system official **Telegram Bot API** par chalta hai.
   - Bot direct channel me messages aur **Clickable Styled Buttons** bhej sakta hai.

3. **Color Prediction Band & Lucky Numbers Added**:
   - Color prediction (Red/Green/Violet) band kar diya gaya hai.
   - Ab sirf **BIG / SMALL** predict hoga aur sath me **Top 2-3 High-Probability Lucky Numbers** (0-9) calculate hoke aayenge.

4. **Separate Messages (No Message Editing)**:
   - Har round ka naya prediction message alag aayega.
   - Result aane par **WIN celebration card** (ya real game screenshot) aur **LOSS recovery alert** alag se post hota hai.

5. **Multi-Game & Multi-Channel Selection**:
   - Channels add karte waqt admin choose kar sakta hai ki kaun sa channel kaun sa game chalayega:
     - ⏱️ **WinGo 30s**
     - ⏱️ **WinGo 1 Min**
     - ⏱️ **WinGo 3 Min**
     - ⏱️ **WinGo 5 Min**
   - Har channel apne selected time duration ke hisab se independent cycle me signals bhejta hai.

6. **Telegram Styled Colored Buttons**:
   - Har prediction post ke sath attractive inline keyboard buttons:
     - `[ 🟢 𝗥𝗘𝗚𝗜𝗦𝗧𝗘𝗥 & 𝗣𝗟𝗔𝗬 (𝗦𝗨𝗖𝗖𝗘𝗦𝗦) 🟢 ]`
     - `[ 🔴 𝗟𝗜𝗩𝗘 𝗥𝗘𝗦𝗨𝗟𝗧 𝗣𝗥𝗢𝗢𝗙 (𝗗𝗔𝗡𝗚𝗘𝗥) 🔴 ]`
     - `[ 🎁 𝗖𝗟𝗔𝗜𝗠 ₹𝟱𝟬𝟬 𝗕𝗢𝗡𝗨𝗦 🎁 ]`
     - `[ 👑 𝗢𝗙𝗙𝗜𝗖𝗜𝗔𝗟 𝗩𝗜𝗣 𝗖𝗛𝗔𝗡𝗡𝗘𝗟 👑 ]`

7. **Martingale Level Protection**:
   - Dynamic Level 1 se Level 5 tracking taaki users safe recovery kar sakein.
   - Win hone par turant Level 1 par reset.

---

## 📁 Project Architecture

```
dee/
├── .env                  # Bot tokens, MongoDB URI, BDGWin credentials
├── config.py             # Configuration & Game URLs loader
├── main.py               # Main bot application runner
├── database/
│   └── mongo.py          # MongoDB channel management & stats
├── engine/
│   └── predictor.py      # AI Trend & Lucky Numbers predictor
├── services/
│   ├── lottery_api.py    # WinGo 30s, 1m, 3m, 5m live fetcher
│   └── bet_automation.py # BDGWin Auto-Bet & Live Screenshot capture
├── bot/
│   ├── handlers.py       # /admin interactive controls
│   ├── keyboards.py      # Styled Channel & Admin keyboards
│   ├── templates.py      # VIP text cards with progress bars
│   ├── scheduler.py      # Multi-game prediction loop
│   └── card_generator.py # Pillow HD win card generator
└── start.bat / start     # Windows / Linux startup scripts
```

---

## 🚀 How to Run

### 1. Install Requirements:
```bash
pip install -r requirements.txt
```

### 2. Configure `.env`:
Credentials automatically configured:
```env
BOT_TOKEN=8030162642:AAG4Gbe2pyQv8ZreGyw8vTEhKvVKY2Eiugw
ADMIN_IDS=8089603563,8015937475
MONGO_URI=mongodb+srv://avinash:avinash12@cluster0.wnwd1fv.mongodb.net/?appName=Cluster0
DEFAULT_REGISTER_LINK=https://bdgwin7.com/#/register?invitationCode=833131014850

# BDGWin Auto-Betting & Win Screenshot Settings
DEMO_AUTO_BET=true
DEMO_LOGIN_URL=https://bdgwina.biz/#/login
DEMO_USERNAME=6556745550
DEMO_PASSWORD=win1222
```

### 3. Start the Bot:
* **Windows**: `python main.py` ya double click `start.bat`
* **Linux/VPS**: `./start`

### 4. Admin Setup (Telegram me):
1. Telegram me bot ko open karke `/start` ya `/admin` bhejein.
2. `➕ Add New Channel` dabayein aur channel ID/username bhejein (jaise `@mywingochannel`).
3. Select karein ki us channel ke liye kaun sa game chalana hai:
   - `[ ⏱️ WinGo 30s ]`
   - `[ ⏱️ WinGo 1 Min ]`
   - `[ ⏱️ WinGo 3 Min ]`
   - `[ ⏱️ WinGo 5 Min ]`
4. Make sure Bot channel me **Administrator** hai messages post karne ke liye.
5. Bot live prediction signals, auto-betting aur real screenshots post karna shuru kar dega!
