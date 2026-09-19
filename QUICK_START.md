# Quick Start - NSE F&O PCS Scanner with Telegram

## 3-Step Setup

### Step 1: Create Telegram Bot

1. Open Telegram and find `@BotFather`
2. Send `/newbot`
3. Follow prompts - you'll get a token like: `123456789:ABCDefGhIjKlMnOpQrStUvWxYz`
4. Start the bot by sending it a message
5. Visit `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` to get your Chat ID

### Step 2: Set Environment Variables

```bash
export TELEGRAM_BOT_TOKEN="123456789:ABCDefGhIjKlMnOpQrStUvWxYz"
export TELEGRAM_CHAT_ID="9876543210"
```

### Step 3: Run Scanner

```bash
python3 scanner_telegram.py
```

## What the Scanner Does

- Analyzes 25 major NSE F&O stocks
- Applies technical filters (RSI, ADX, Volume, Support levels)
- Identifies Put Credit Spread (PCS) trading opportunities
- Sends results to your Telegram chat
- Takes ~30-60 seconds to complete

## Output Example

**In Console:**
```
🚀 Starting NSE F&O PCS Scanner...
⏰ Time: 2026-09-19 09:15:13 IST

📊 Scanning 25 stocks...

[ 1/25] Analyzing RELIANCE       ... ✅ (87% HIGH)
[ 2/25] Analyzing TCS            ... ✅ (76% MEDIUM)

✅ Found 8 stocks with confirmed patterns!

 1. RELIANCE    | Strength:    87% | Confidence:    HIGH
 2. TCS         | Strength:    76% | Confidence: MEDIUM
```

**On Telegram:**
```
🚀 NSE F&O PCS SCAN RESULTS

📊 Scan Summary
📅 Time: 2026-09-19 09:15 IST
✅ Stocks Found: 8
🏆 High Confidence: 3
🟡 Medium Confidence: 5

📋 Stocks Sorted by Strength

 1. RELIANCE - 87% (HIGH)
    Price: ₹2456.75 | RSI: 52.3 | ADX: 28.4 | Vol: 1.8x

 2. TCS - 76% (MEDIUM)
    Price: ₹3847.50 | RSI: 48.1 | ADX: 24.2 | Vol: 1.5x
```

## Scheduling

### Daily Execution with Cron

Edit crontab:
```bash
crontab -e
```

Add this line to run at 9:15 AM IST daily:
```
15 9 * * * export TELEGRAM_BOT_TOKEN="YOUR_TOKEN"; export TELEGRAM_CHAT_ID="YOUR_ID"; cd /home/user/nsepcs && python3 scanner_telegram.py
```

### Using Screen for Background Execution

```bash
screen -S nse_scanner
export TELEGRAM_BOT_TOKEN="YOUR_TOKEN"
export TELEGRAM_CHAT_ID="YOUR_ID"
python3 scanner_telegram.py
# Press Ctrl+A then D to detach
```

## Filter Criteria Applied

| Filter | Value | Purpose |
|--------|-------|---------|
| RSI | 30-75 | Neutral to slight overbought |
| ADX | > 20 | Trend confirmation |
| Volume | > 1.2x avg | Institutional participation |
| Support | < 3% distance | Good entry point |

## Stocks Monitored

**Tier 1 (Most Liquid):** NIFTY50, BANKNIFTY, RELIANCE, TCS, HDFCBANK, INFY, ICICIBANK, SBIN, LT, ITC

**Tier 2:** KOTAKBANK, AXISBANK, HCLTECH, WIPRO, MARUTI, ASIANPAINT, BHARTIARTL, SUNPHARMA, TATAMOTORS, ADANIENT

**Tier 3:** BAJFINANCE, BAJAJFINSV, INDUSINDBK, TECHM, TITAN

## Troubleshooting

**Q: "Telegram credentials not configured"**
- Ensure both `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set
- Test with: `python3 -c "import os; print(os.getenv('TELEGRAM_BOT_TOKEN'))"`

**Q: "No stocks found"**
- Run during market hours (9:15 AM - 3:30 PM IST)
- Check if Yahoo Finance is accessible from your network
- Verify internet connectivity

**Q: Script runs but no Telegram message**
- Verify bot token and chat ID are correct
- Test bot manually: `curl https://api.telegram.org/bot<TOKEN>/getMe`
- Check if bot is still active in your Telegram account

## Advanced Usage

### Custom Stock List

Edit `DEFAULT_STOCKS` in `scanner_telegram.py`:
```python
DEFAULT_STOCKS = [
    'RELIANCE', 'TCS', 'INFY', 'HDFCBANK',
    # Add your stocks here
]
```

### Modify Filters

Edit filter values in `analyze_stock()` function:
```python
if not (30 <= current_rsi <= 75):   # Adjust RSI range
if current_adx < 20:                # Adjust ADX threshold
if volume_ratio < 1.2:              # Adjust volume requirement
```

## Files Included

- `scanner_telegram.py` - Main scanner script (recommended)
- `run_scanner.py` - Alternative implementation
- `SCANNER_TELEGRAM_SETUP.md` - Detailed setup guide
- `QUICK_START.md` - This file

## Support

For issues or questions, refer to:
1. `SCANNER_TELEGRAM_SETUP.md` - Comprehensive troubleshooting guide
2. Console output - Check for error messages
3. Telegram test - Verify bot and chat ID manually

## Next Steps

1. ✅ Set up Telegram bot
2. ✅ Export environment variables
3. ✅ Run `python3 scanner_telegram.py`
4. ✅ Check results in Telegram
5. ✅ Schedule with cron for daily execution

**Happy Trading! 📈**

---

*Disclaimer: This scanner is for educational purposes. Not financial advice. Always do your own research and consult qualified advisors before trading.*
