# Quick Start - Telegram Scanner

Get stocks meeting filter criteria sent to your Telegram in 5 minutes!

## 🚀 Fastest Start (No Setup)

Just want to test it? Run the demo:

```bash
cd /home/user/nsepcs
python3 telegram_scanner_demo.py
```

✅ Works offline, shows sample results with 4 qualifying stocks

---

## 📱 Setup Telegram (5 minutes)

### 1️⃣ Create Bot in Telegram

```
1. Open Telegram → Search "BotFather"
2. Send: /newbot
3. Give bot a name
4. Copy TOKEN (you'll need this)
```

### 2️⃣ Get Your Chat ID

```
1. Send message to your new bot
2. Visit in browser:
   https://api.telegram.org/botYOUR_TOKEN_HERE/getUpdates

3. Find your chat ID in response (number after "id":)
```

### 3️⃣ Run Scanner

```bash
# Set your credentials
export TELEGRAM_BOT_TOKEN="123456:ABC-DEF1234..."
export TELEGRAM_CHAT_ID="987654321"

# Run scanner
cd /home/user/nsepcs
python3 simple_telegram_scanner.py
```

🎉 Results will be sent to your Telegram!

---

## 🔄 Automate Daily (Optional)

Add to your crontab to run at 3:40 PM IST daily:

```bash
crontab -e

# Add this line:
40 15 * * 1-5 cd /home/user/nsepcs && TELEGRAM_BOT_TOKEN="YOUR_TOKEN" TELEGRAM_CHAT_ID="YOUR_ID" python3 simple_telegram_scanner.py >> /tmp/scanner.log 2>&1
```

---

## ⚙️ Adjust Filters

Make results more strict or relaxed:

```bash
# STRICT (fewer, high-quality stocks)
export MIN_ADX="25"
export MIN_RSI="40"
export MIN_RSI_MAX="70"
export MIN_VOLUME_RATIO="1.5"

# RELAXED (more results)
export MIN_ADX="15"
export MIN_RSI="30"
export MIN_RSI_MAX="75"
export MIN_VOLUME_RATIO="1.0"
```

---

## 📊 What Gets Sent

For each qualifying stock:
- 💰 Current price
- 📈 RSI (momentum indicator)
- ⚡ ADX (trend strength)
- 📊 Volume ratio
- 🎯 Overall score (0-100)
- 🟢🔴 Bullish/Bearish signal

---

## 🆘 Troubleshooting

**Q: "Telegram not configured"**  
A: Set BOT_TOKEN and CHAT_ID environment variables

**Q: "No results"**  
A: Adjust MIN_RSI, MIN_ADX, or MIN_VOLUME_RATIO to be less strict

**Q: Network error?**  
A: Use demo version: `python3 telegram_scanner_demo.py`

**Q: Which scanner to use?**  
- **Demo** → Testing, no network needed
- **Simple** → Real data, lightweight (recommended)
- **Advanced** → Full features, slower

---

## 📚 Full Documentation

See `TELEGRAM_SCANNER_README.md` for:
- Detailed setup instructions
- All configuration options
- Multiple daily runs
- Troubleshooting guide
- Performance details

---

## ⚡ One-Liner Quick Test

```bash
cd /home/user/nsepcs && python3 telegram_scanner_demo.py
```

That's it! You'll see qualifying stocks printed on screen. 🎉
