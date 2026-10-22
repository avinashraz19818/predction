# 🚀 VPS Deployment & Setup Guide (Ubuntu / Debian)

Yeh guide use karke aap apne Linux/Ubuntu VPS par **WinGo VIP Prediction Bot** ko 2 minute me install aur background me 24/7 run kar sakte hain.

---

## 📋 1. Quick One-Line Setup (Sab Kuch Ek Sath)

Agar aap fresh VPS par hain to direct yeh commands copy-paste karein:

```bash
# 1. Update system & install dependencies
sudo apt update && sudo apt install -y python3 python3-pip python3-venv git chromium-browser chromium-chromedriver

# 2. Clone Repository
git clone https://github.com/avinashraz19818/predction.git
cd predction

# 3. Virtual Environment setup
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4. Create .env Configuration File
cat << 'EOF' > .env
BOT_TOKEN=8030162642:AAG4Gbe2pyQv8ZreGyw8vTEhKvVKY2Eiugw
ADMIN_IDS=8089603563,8015937475

MONGO_URI=mongodb+srv://avinash:avinash12@cluster0.wnwd1fv.mongodb.net/?appName=Cluster0
MONGO_DB_NAME=maxie1min

DEFAULT_REGISTER_LINK=https://bdgwin7.com/#/register?invitationCode=833131014850
DEFAULT_PROMO_TEXT=🔥 Maintain 3-5 Level Fund for 100% Daily Profit!

DEMO_AUTO_BET=true
DEMO_LOGIN_URL=https://bdgwina.biz/#/login
DEMO_USERNAME=6556745550
DEMO_PASSWORD=win1222
EOF

# 5. Make start script executable & Run Bot in Background
chmod +x start
./start
```

---

## 🔄 2. Existing VPS par Code Update (Git Pull) Kaise Karein?

Agar aapne pehle se clone kiya hua hai aur sirf naya code pull karna hai:

```bash
cd predction
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt
./start
```

---

## 🛠️ 3. Daily Useful Management Commands

### 📜 Live Logs Check Karna:
Bot real-time me kya kar raha hai (signals, predictions, screenshots) dekhne ke liye:
```bash
tail -f bot.log
```
*(Log band karne ke liye keyboard par `Ctrl + C` dabayein)*

### 🛑 Bot ko Stop / Kill Karna:
```bash
kill $(cat bot.pid) 2>/dev/null || pkill -f main.py
```

### ⚡ Bot ko Restart Karna:
```bash
./start
```

### 🔍 Check Karna ki Bot Chal Raha Hai ya Nahi:
```bash
ps aux | grep main.py
```

---

## 📱 4. Telegram me Bot Setup Kaise Karein?

1. Telegram par apne bot ko open karein: `https://t.me/YOUR_BOT_USERNAME`
2. Bot ko `/start` ya `/admin` command bhejein.
3. `➕ Add New Channel` par click karein.
4. Apne channel ka username ya ID bhejein (Jaise: `@mywingochannel`).
5. WinGo Duration select karein:
   - `⏱️ WinGo 30s`
   - `⏱️ WinGo 1 Min`
   - `⏱️ WinGo 3 Min`
   - `⏱️ WinGo 5 Min`
6. Make sure Bot aapke channel me **Administrator** hai with "Post Messages" permission.
7. Bot turant live prediction signals aur screenshots post karna start kar dega!
