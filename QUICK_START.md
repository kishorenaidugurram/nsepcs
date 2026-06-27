# 🚀 Quick Start - Run Scanner & Send to Telegram

Get results sent to Telegram in 2 minutes!

## Prerequisites
- Python 3.8+
- Telegram account
- Internet connection

## Setup (First Time Only)

### 1️⃣ Create Telegram Bot (1 minute)
```
In Telegram:
1. Search for @BotFather
2. Send: /newbot
3. Choose a name: "Stock Scanner"
4. Choose a username: "my_stock_scanner_bot"
5. Copy the TOKEN you receive
```

### 2️⃣ Get Your Chat ID (30 seconds)
```
In Telegram:
1. Search for @userinfobot
2. Send any message
3. Copy the ID you receive
```

### 3️⃣ Set Environment Variables

**Linux/Mac:**
```bash
export TELEGRAM_BOT_TOKEN='paste_bot_token_here'
export TELEGRAM_CHAT_ID='paste_chat_id_here'
```

**Windows (Command Prompt):**
```cmd
set TELEGRAM_BOT_TOKEN=paste_bot_token_here
set TELEGRAM_CHAT_ID=paste_chat_id_here
```

**Windows (PowerShell):**
```powershell
$env:TELEGRAM_BOT_TOKEN='paste_bot_token_here'
$env:TELEGRAM_CHAT_ID='paste_chat_id_here'
```

### 4️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

## Run the Scanner

**Linux/Mac:**
```bash
./run_scanner.sh
```

**Windows:**
Double-click `run_scanner.bat`

**Or anywhere:**
```bash
python3 run_scanner_with_telegram.py
```

## That's it! ✅

The scanner will:
- Scan NSE F&O stocks for trading patterns
- Find stocks with strong technical setups
- Send results to your Telegram
- Save results to CSV

## What You'll Get

Example Telegram message:
```
📈 NSE F&O Stock Scanner Results
Generated: 2024-06-27 14:30:00 IST

1. RELIANCE 🟢
   Price: ₹2845.50
   Pattern: Current Day Breakout
   Strength: 92% | Success: 78%
   RSI: 65.2 | ADX: 28.5 | Vol: 2.5x

2. INFY 🟢
   Price: ₹1520.25
   Pattern: Cup and Handle
   ...
```

## Troubleshooting

**"Failed to send to Telegram"**
→ Check bot token and chat ID (no extra spaces)

**"No data available"**
→ Check internet connection

**"No module named 'ta'"**
→ Make sure you have the ta.py file (it should be there)

**"Python not found"**
→ Install Python from https://www.python.org/

## Advanced Options

See `TELEGRAM_SCANNER_SETUP.md` for:
- Understanding results
- Scheduling automated scans
- Customizing filters
- Running on a VPS

---

**Questions?** Check the detailed setup guide: `TELEGRAM_SCANNER_SETUP.md`
