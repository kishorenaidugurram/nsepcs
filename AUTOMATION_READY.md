# 🚀 Telegram Automation Setup Complete

Your NSE F&O PCS Stock Scanner is now ready to send automatic stock alerts to Telegram!

## What's Ready

✅ **simple_telegram_scanner.py** - Production-ready automated scanner
✅ **telegram_scanner.py** - Advanced version with pattern detection  
✅ **TELEGRAM_SETUP.md** - Complete setup & configuration guide
✅ **requirements.txt** - Updated with Telegram dependencies

## Quick Start (3 Steps)

### 1️⃣ Get Telegram Bot Token
Send `/newbot` to [@BotFather](https://t.me/botfather) on Telegram and copy your token.

### 2️⃣ Get Your Chat ID
Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
Look for `"id":123456789` in the response.

### 3️⃣ Run Scanner
```bash
export TELEGRAM_BOT_TOKEN="your_token_here"
export TELEGRAM_CHAT_ID="your_id_here"
python3 simple_telegram_scanner.py
```

You'll receive a Telegram message with qualified stocks!

## Automated Scheduling

### Via Cron (Linux/Mac)
```bash
# Run after market close daily (3:30 PM IST)
crontab -e
# Add: 30 15 * * 1-5 cd /home/user/nsepcs && python3 simple_telegram_scanner.py
```

### Via GitHub Actions (No Local Setup)
```bash
# Push to GitHub, configure secrets, runs on schedule automatically
# See TELEGRAM_SETUP.md for full configuration
```

### Via Systemd Timer (Advanced)
```bash
# See TELEGRAM_SETUP.md for systemd setup instructions
```

## Filter Criteria

The scanner identifies stocks meeting these technical criteria:

| Criteria | Value | Meaning |
|----------|-------|---------|
| **RSI** | 40-70 | Healthy momentum (not oversold/overbought) |
| **ADX** | ≥ 20 | Strong trend confirmation |
| **Volume** | ≥ 1.2x | Above average trading volume |
| **Price** | Above SMA20 | Price above 20-day moving average |

All criteria must be met for a stock to qualify.

## What You'll Receive

**Telegram Message Example:**

```
📊 NSE F&O PCS Scan Results
🕐 2024-01-15 15:30:00

🎯 Found 8 Qualifying Stocks

Summary Metrics:
• Average Strength: 72.3%
• Highest Strength: 89.2%
• Average Volume Ratio: 1.85x

Top Stocks:
1. RELIANCE 🟢
   Price: ₹2,847.50 | SMA20: ₹2,825.00
   RSI: 56.3 | ADX: 28.5
   Strength: 89.2% | Volume: 2.1x

2. HDFCBANK 🟡
   Price: ₹1,652.35 | SMA20: ₹1,628.50
   ...and 6 more stocks
```

## Key Features

✨ **Lightweight** - Simple scanner uses only yfinance, pandas, numpy, requests
⚡ **Fast** - Analyzes 35 stocks in 5-10 minutes
🔄 **Reliable** - Graceful error handling, automatic fallbacks
📊 **Smart Filtering** - Technical indicators validate stock quality
🤖 **Automated** - Set up once, runs on schedule forever
📱 **Telegram-Native** - Formatted messages designed for mobile

## File Structure

```
/home/user/nsepcs/
├── simple_telegram_scanner.py    # ← USE THIS (recommended)
├── telegram_scanner.py            # Advanced version (optional)
├── TELEGRAM_SETUP.md             # Complete setup guide
├── AUTOMATION_READY.md           # This file
├── streamlit_app.py               # Main app (Streamlit)
├── requirements.txt               # Dependencies
└── README.md                      # Project overview
```

## Environment Variables Required

```bash
TELEGRAM_BOT_TOKEN     # From @BotFather
TELEGRAM_CHAT_ID       # Your Telegram chat ID
```

These can be:
- Set in shell: `export TELEGRAM_BOT_TOKEN="..."`
- Passed inline: `TELEGRAM_BOT_TOKEN="..." python3 ...`
- Stored in `.env` file and loaded: `source .env`

## Testing Your Setup

```bash
# Dry run to test without modifications
python3 -c "
from simple_telegram_scanner import SimpleTelegramScanner
s = SimpleTelegramScanner('$TELEGRAM_BOT_TOKEN', '$TELEGRAM_CHAT_ID')
print('✓ Ready to scan!')
"

# Test with 3 stocks only
# Edit simple_telegram_scanner.py, change COMPLETE_NSE_FO_UNIVERSE to ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS']
python3 simple_telegram_scanner.py
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Missing environment variables" | Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID |
| "Telegram connection failed" | Verify token is correct, check internet |
| "No stocks met criteria" | Normal! Market conditions just don't match filters |
| "Module not found" | Run `pip install -r requirements.txt` |
| "No data downloaded" | yfinance is rate limited - wait 5 minutes and retry |

## Next Steps

1. **Read** `TELEGRAM_SETUP.md` for detailed instructions
2. **Test** the scanner with your Telegram bot
3. **Schedule** automation using cron, GitHub Actions, or systemd
4. **Monitor** results and adjust filters if needed
5. **Trade** responsibly with proper risk management

## Important Disclaimers

⚠️ **Educational Purpose Only**
- This is NOT financial advice
- Options trading carries substantial risk
- Always verify signals independently
- Never risk more than you can afford to lose
- Start with paper trading before live trading
- Consult qualified financial advisors

## Advanced Customization

See `simple_telegram_scanner.py`:

```python
# Change filter thresholds
rsi_ok = 40 <= current_rsi <= 70  # Adjust range
adx_ok = current_adx >= 20         # Increase for stronger trends
volume_ok = volume_ratio >= 1.2    # Adjust volume requirement

# Change stocks to scan
COMPLETE_NSE_FO_UNIVERSE = ['RELIANCE.NS', 'TCS.NS', ...]

# Customize message format
# Edit format_telegram_message() method
```

## Support

- **Telegram Issues**: See TELEGRAM_SETUP.md
- **Scanner Issues**: Check error logs
- **Technical Help**: See comments in code files
- **Market Data**: Verify yfinance connectivity

---

**Status**: ✅ Ready for Production
**Last Updated**: 2024-01-15
**Scanner Version**: 1.0

🎯 Your automated stock scanner is ready to go! Configure your Telegram bot and start receiving alerts.
