# NSE F&O PCS Scanner - CLI Setup Guide

## Overview

The scanner scripts allow you to run the PCS (Put Credit Spread) screening automation outside of the Streamlit web interface. This is useful for scheduled/automated scanning and sending results directly to Telegram.

## Available Scanners

### 1. `scanner_demo.py` - Demo with Sample Data
- **Purpose**: Test and demonstrate the scanner without needing market data
- **Use Case**: Verify Telegram integration setup
- **Run**: `python scanner_demo.py`

### 2. `scanner_standalone.py` - Production Scanner
- **Purpose**: Real scanner that fetches live market data and analyzes stocks
- **Use Case**: Scheduled scanning, automated alerts
- **Run**: `python scanner_standalone.py`

## Setup Instructions

### Step 1: Telegram Bot Setup

1. **Create a Telegram Bot**:
   - Open Telegram
   - Search for `@BotFather`
   - Send `/start` then `/newbot`
   - Follow prompts to create a bot
   - Save your `BOT_TOKEN`

2. **Get Your Chat ID**:
   - Search for `@userinfobot` on Telegram
   - Send `/start`
   - It will show your Chat ID
   - Save your `CHAT_ID`

### Step 2: Set Environment Variables

```bash
export TELEGRAM_BOT_TOKEN='your_bot_token_here'
export TELEGRAM_CHAT_ID='your_chat_id_here'
```

Or add to your `.bashrc` / `.bash_profile`:

```bash
echo "export TELEGRAM_BOT_TOKEN='your_bot_token'" >> ~/.bashrc
echo "export TELEGRAM_CHAT_ID='your_chat_id'" >> ~/.bashrc
source ~/.bashrc
```

### Step 3: Test the Setup

Run the demo to verify Telegram is configured:

```bash
python scanner_demo.py
```

You should see:
```
✅ Successfully sent to Telegram!
```

### Step 4: Run the Actual Scanner

To run the live scanner:

```bash
# Basic scan (Nifty 50 stocks)
python scanner_standalone.py

# Scan without Telegram (for testing)
python scanner_standalone.py --no-telegram

# Custom volume threshold
python scanner_standalone.py --min-volume 1.5
```

## Scanner Options

```bash
python scanner_standalone.py --help
```

Available options:
- `--no-telegram`: Skip Telegram notification
- `--bot-token`: Telegram bot token (or use env var)
- `--chat-id`: Telegram chat ID (or use env var)
- `--min-volume`: Minimum volume ratio threshold (default: 1.2)

## Scheduling Automated Scans

### Using Cron (Linux/Mac)

Edit your crontab:

```bash
crontab -e
```

Add this line to run scanner at 3:30 PM daily:

```bash
30 15 * * 1-5 cd /home/user/nsepcs && python scanner_standalone.py >> scanner.log 2>&1
```

Or to run every 2 hours on trading days:

```bash
0 9-16 * * 1-5 cd /home/user/nsepcs && python scanner_standalone.py >> scanner.log 2>&1
```

### Using Docker (Optional)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY scanner_standalone.py .
ENV TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
ENV TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID}
CMD ["python", "scanner_standalone.py"]
```

## Understanding Scanner Output

### Console Output Example

```
🚀 Starting NSE F&O Scanner...
⏰ 2026-08-17 03:44:09 IST
📊 Scanning 50 stocks...
  [50/50] HINDUNILVR...✅ Scan complete! Found 6 stocks

==================================================
RESULTS
==================================================
RELIANCE     ₹3087.45 RSI:58.3 ADX:22.8 Vol:1.45x Strength:78.5% HIGH
TCS          ₹3652.10 RSI:52.1 ADX:24.2 Vol:1.32x Strength:72.3% MEDIUM
HDFCBANK     ₹1658.75 RSI:55.6 ADX:21.5 Vol:1.28x Strength:68.9% MEDIUM
INFY         ₹2821.50 RSI:48.2 ADX:23.1 Vol:1.41x Strength:75.2% HIGH
ICICIBANK    ₹1042.30 RSI:61.4 ADX:20.9 Vol:1.19x Strength:65.7% MEDIUM
BHARTIARTL   ₹1389.60 RSI:54.8 ADX:25.3 Vol:1.55x Strength:81.2% HIGH

💾 Saved to: scan_results_20260817_034344.json
```

### Telegram Message Format

The scanner sends a nicely formatted Telegram message with:
- ✓ Summary statistics
- ✓ Qualifying stocks list
- ✓ Technical metrics (RSI, ADX, Volume)
- ✓ Pattern detections
- ✓ Confidence indicators (🟢 HIGH, 🟡 MEDIUM, 🔴 LOW)

## Troubleshooting

### Issue: "Telegram credentials not found"

**Solution**: Set environment variables

```bash
export TELEGRAM_BOT_TOKEN='your_token'
export TELEGRAM_CHAT_ID='your_id'
```

Verify:
```bash
echo $TELEGRAM_BOT_TOKEN
echo $TELEGRAM_CHAT_ID
```

### Issue: "No stocks met the criteria today"

**Possible Causes**:
- Market conditions don't match technical filters
- Network connectivity issues fetching data
- Too strict filter settings

**Solution**:
- Run demo: `python scanner_demo.py`
- Check network: `curl https://query1.finance.yahoo.com`
- Lower min volume: `--min-volume 1.0`

### Issue: "Failed to get ticker"

**Cause**: Network connectivity or data source issues

**Solutions**:
1. Check internet: `ping 8.8.8.8`
2. Verify proxy settings if behind corporate network
3. Use demo mode to test: `python scanner_demo.py`

## Important Notes

⚠️ **Disclaimers**:
- This is NOT financial advice
- These stocks show technical setups suitable for Put Credit Spreads
- Always verify results with your own analysis
- Never trade without proper risk management
- Paper trade first before live trading

## Scanner Logic

The scanner evaluates stocks based on:

1. **Technical Filters**:
   - RSI: 30-75 (neutral momentum)
   - ADX: >20 (trend strength)
   - Price above 97% of SMA20 (support)

2. **Volume Confirmation**:
   - Current volume >1.2x average
   - Indicates institutional participation

3. **Bullish Patterns**:
   - Price near 20-day high
   - Price above moving averages
   - Rising RSI (not overbought)
   - Above-average volume

4. **Strength Scoring**:
   - Combines pattern matches and technical metrics
   - Calculates overall pattern strength (0-100%)

## Support

For issues or questions:
1. Check this guide
2. Review scanner output logs
3. Test with demo mode
4. Verify Telegram bot token and chat ID

## Next Steps

1. ✅ Set up Telegram bot and chat ID
2. ✅ Export environment variables
3. ✅ Test with demo: `python scanner_demo.py`
4. ✅ Run live scanner: `python scanner_standalone.py`
5. ✅ Setup cron for scheduling
6. ✅ Monitor for alerts

---

**Happy Trading! 📈**

*Remember: This scanner identifies technical setups, not buy/sell signals. Always combine with fundamental analysis and risk management.*
