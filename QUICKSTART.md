# Quick Start - Run Scanner & Send Results to Telegram

## 1️⃣ Get Your Telegram Credentials (2 minutes)

### Create a Telegram Bot:
- Open Telegram → Search for `@BotFather`
- Send `/newbot`
- Follow instructions
- **Copy the token** (you'll get something like `123456:ABC-DEF1234...`)

### Get Your Chat ID:
- Message your bot (send any text)
- Visit: `https://api.telegram.org/bot<PASTE_YOUR_TOKEN>/getUpdates`
- Find your `chat ID` (a number like `987654321`)

## 2️⃣ Set Environment Variables

```bash
export TELEGRAM_BOT_TOKEN="your_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

## 3️⃣ Run the Scanner

```bash
# Go to project directory
cd /path/to/nsepcs

# Run the scanner
python3 run_scanner_simple.py --max-stocks 50
```

## ✅ What Happens

1. Scanner analyzes 50 NSE F&O stocks
2. Finds stocks matching technical criteria (RSI, ADX, Volume, Patterns)
3. **Sends results to your Telegram in real-time** 📱
4. Saves results to JSON file locally

## 📊 Sample Output in Telegram

```
📊 Stock Scanner Results
Time: 28-Jun 15:30 IST
Found: 15 stocks

1. RELIANCE
  Price: ₹2650.50 | Vol: 1.8x | RSI: 55
  Strength: 82% | Patterns: Current Day Breakout

2. TCS
  Price: ₹3520.25 | Vol: 1.5x | RSI: 62
  Strength: 78% | Patterns: Cup and Handle

... and 13 more stocks
```

## 🎯 Filter Options

```bash
# Aggressive (find more stocks)
python3 run_scanner_simple.py --rsi-min 25 --adx-min 15 --strength-min 60

# Conservative (high quality only)
python3 run_scanner_simple.py --rsi-min 40 --adx-min 25 --strength-min 75

# Scan all F&O stocks
python3 run_scanner_simple.py

# Custom combination
python3 run_scanner_simple.py --max-stocks 100 --volume-ratio 1.0 --strength-min 70
```

## ⚠️ Network Issue in Remote Environment

This remote cloud environment blocks external APIs. **The scanner won't work here** due to network policy.

**Solution**: Run on your local machine where you have internet access.

### Steps to run locally:

1. Clone/download the project
2. Install Python 3.8+
3. Install dependencies: `pip install -r requirements.txt`
4. Set environment variables
5. Run: `python3 run_scanner_simple.py`

## 📚 More Options

For advanced usage, see `TELEGRAM_SETUP_GUIDE.md`

## Support

**Problem**: Telegram not sending
- Check your token and chat ID
- Verify internet connection
- Test bot works: Send message directly in Telegram

**Problem**: No stocks found
- Decrease filter strictness
- Increase `--max-stocks`
- Lower `--strength-min` value

---

Ready to find the next breakout? 🚀
