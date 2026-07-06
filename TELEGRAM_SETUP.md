# NSE F&O Scanner - Telegram Integration Setup

This guide shows how to set up the NSE F&O stock scanner to send results to Telegram.

## Quick Start (5 minutes)

### 1. Create a Telegram Bot

Go to [@BotFather](https://t.me/botfather) on Telegram and:
- Type `/newbot`
- Give it a name (e.g., "NSE Stock Scanner")
- You'll get a **BOT TOKEN** that looks like:
  ```
  1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh
  ```

### 2. Get Your Chat ID

Go to [@userinfobot](https://t.me/userinfobot) and it will show your **CHAT ID** (a number like `123456789`)

### 3. Setup Credentials

Option A: **Automatic (Recommended)**
```bash
bash setup_telegram.sh
```

Option B: **Manual**
```bash
# Create .env file
cat > .env << EOF
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
EOF
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
# Or if issues with 'ta':
pip install yfinance pandas numpy requests python-dotenv
```

### 5. Run Scanner

```bash
python simple_scanner.py
```

Or with Telegram integration:
```bash
python run_scanner_telegram.py
```

## Filters & Customization

Edit `simple_scanner.py` to customize filters:

```python
filters = {
    'rsi_min': 35,           # RSI lower bound (0-100)
    'rsi_max': 70,           # RSI upper bound (0-100)
    'volume_ratio': 1.2,     # Volume must be ≥ 1.2x of 20-day average
    'min_score': 60          # Stock must score ≥60/100
}
```

## Filter Explanations

| Filter | Meaning | Default | Notes |
|--------|---------|---------|-------|
| **RSI** | Relative Strength Index (momentum) | 35-70 | 30-50: oversold, 70-100: overbought |
| **Volume Ratio** | Current volume vs 20-day avg | 1.2x | Higher = more trading activity |
| **Min Score** | Composite score out of 100 | 60 | Higher = stronger signals |

## What Gets Scored

Each stock gets points for:
- ✅ RSI in range (25 points)
- ✅ Price > 20-day MA (20 points)
- ✅ 20-day MA > 50-day MA (20 points)
- ✅ MACD bullish (15 points)
- ✅ High volume (20 points)

Maximum = 100 points

## Sample Output

```
============================================================
🚀 NSE F&O Stock Scanner
============================================================
✅ Found 12 qualifying stocks

Top stocks by score:
  RELIANCE.NS - Score: 95, RSI: 52.3, Vol: 2.15x
  TCS.NS      - Score: 88, RSI: 48.7, Vol: 1.89x
  INFY.NS     - Score: 82, RSI: 55.2, Vol: 1.65x

📱 Sending results to Telegram...
✅ Results sent to Telegram!
```

## Telegram Message

You'll receive a message in Telegram with:
- 📊 Date & Time (IST)
- 📈 List of qualifying stocks
- 💰 Price for each stock
- 📈 Score, RSI, Volume ratio
- ✨ Signals detected

## Troubleshooting

### "Telegram not configured"
- Make sure `.env` file exists in the project directory
- Verify `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set
- Check with: `cat .env`

### "No stocks found"
- Filters might be too strict
- Try lowering `min_score` from 60 to 50
- Increase `rsi_max` from 70 to 75
- Decrease `volume_ratio` from 1.2 to 1.0

### "Connection error / timeout"
- Yahoo Finance might be temporarily down
- Check internet connection
- Retry in a few minutes

### "Bot doesn't respond"
- Check BOT_TOKEN is correct (no spaces)
- Verify CHAT_ID is a number (not a username)
- Make sure bot is not already running elsewhere

## Advanced: Schedule Daily Scans

### Linux/Mac

```bash
# Edit crontab
crontab -e

# Add this line to run at 9:30 AM IST (4:00 AM UTC) every weekday
0 4 * * 1-5 cd /path/to/nsepcs && python simple_scanner.py >> scanner.log 2>&1
```

### Windows

Use Task Scheduler:
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily at 9:30 AM
4. Set action: `python C:\path\to\nsepcs\simple_scanner.py`

## API Rate Limits

- Yahoo Finance: ~2000 requests/hour (50 stocks = ~10 seconds)
- Telegram: 30 messages/second (no issue)

## Security Notes

⚠️ **Important:**
- Never commit `.env` file to git (it has credentials)
- `.env` is already in `.gitignore`
- Keep your BOT_TOKEN and CHAT_ID secret
- Use different bots for different purposes

## CSV Export

Results are automatically saved to:
```
scanner_results_YYYYMMDD_HHMMSS.csv
```

Import into Excel for further analysis.

## Performance

- 50 stocks: ~30 seconds
- 100 stocks: ~60 seconds
- 208 stocks (full universe): ~3-4 minutes

This can be optimized with parallel requests if needed.

## Support

For issues:
1. Check filters are reasonable
2. Verify internet connection
3. Ensure dependencies installed: `pip list | grep -E "yfinance|pandas|requests"`
4. Check if Yahoo Finance is accessible: `python -c "import yfinance as yf; print(yf.Ticker('INFY.NS').info)"`

## Next Steps

- [ ] Create Telegram bot
- [ ] Get your Chat ID
- [ ] Run `bash setup_telegram.sh`
- [ ] Run `python simple_scanner.py`
- [ ] Check Telegram for results
- [ ] Customize filters as needed
- [ ] Set up scheduled daily scans

Happy screening! 📈
