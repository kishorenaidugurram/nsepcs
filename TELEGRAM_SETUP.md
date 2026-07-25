# NSE F&O PCS Screening - Telegram Automation Setup

## Overview

`scan_and_notify.py` is an automated script that:
1. Screens NSE F&O stocks for high-probability Put Credit Spread (PCS) setups
2. Filters results by pattern strength score (default: 55+)
3. Sends results directly to Telegram

## Quick Start

### Step 1: Get Telegram Bot Token

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow the prompts
3. Choose a name (e.g., "NSE PCS Scanner")
4. You'll receive a **BOT_TOKEN** (e.g., `123456789:ABCdef-GhIjKlMnOpQrStUvWxYz`)

### Step 2: Get Your Chat ID

1. Search for `@userinfobot` in Telegram
2. Send `/start` 
3. You'll receive your **Chat ID** (e.g., `987654321`)

Alternatively, send any message to your bot and run:
```bash
curl https://api.telegram.org/bot<BOT_TOKEN>/getUpdates
```
Look for `"id"` in the response under `"chat"`.

### Step 3: Configure Environment Variables

**Option A: Set environment variables (temporary)**
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
python scan_and_notify.py
```

**Option B: Create `.env` file (persistent)**
```bash
cat > /home/user/nsepcs/.env << EOF
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
EOF

# Load and run
source .env
python scan_and_notify.py
```

**Option C: Add to systemd timer (recommended for scheduling)**
See "Scheduling with Systemd" below.

## Running the Script

### Manual Run
```bash
python scan_and_notify.py
```

### With Custom Filters
Edit the script and modify these variables:
```python
DEFAULT_MIN_SCORE = 55      # Minimum pattern strength (0-100)
DEFAULT_MIN_RSI = 30        # Minimum RSI
DEFAULT_MAX_RSI = 75        # Maximum RSI
DEFAULT_MIN_ADX = 20        # Minimum ADX for trend strength
```

## Scheduling with Cron

Add to crontab to run daily before market close (e.g., 3:30 PM IST):

```bash
crontab -e
```

Add this line:
```cron
0 15 * * 1-5 export TELEGRAM_BOT_TOKEN="your_token" && export TELEGRAM_CHAT_ID="your_id" && cd /home/user/nsepcs && python scan_and_notify.py >> /var/log/nse-pcs-scan.log 2>&1
```

(M-F, 3:00 PM IST)

## Expected Output

### Console Output:
```
============================================================
NSE F&O PCS SCREENING & TELEGRAM NOTIFICATION
============================================================

🔍 Screening 39 stocks for high-probability PCS setups...
  [1/39] Analyzing RELIANCE.NS...
  [2/39] Analyzing TCS.NS...
  ...

📊 TOP RESULTS:
------------------------------------------------------------
1. STOCK1    Score: 75.2/100 RSI:  55.3 ADX: 25.4
2. STOCK2    Score: 68.9/100 RSI:  48.2 ADX: 22.1
3. STOCK3    Score: 65.1/100 RSI:  52.7 ADX: 20.8

💾 Results saved to: /tmp/nse_pcs_results_20260725_153045.csv

📱 Sending Telegram notification...
✅ Message sent successfully to Telegram!

============================================================
Scan completed: 3 high-probability setups found
============================================================
```

### Telegram Message Format:
```
📊 NSE F&O PCS SCREENING RESULTS
2026-07-25 15:30 IST

🎯 High-Probability Setups Found: 3

1. RELIANCE.NS
Score: 75.2/100 | RSI: 55.3 | ADX: 25.4
Price: ₹2,850.50 | SMA20: ₹2,820.30
Signals: RSI optimal: 55.3, Strong trend: ADX 25.4

2. TCS.NS
Score: 68.9/100 | RSI: 48.2 | ADX: 22.1
Price: ₹4,120.00 | SMA20: ₹4,095.50
Signals: Price above SMA20, Above average volume: 1.45x

...

Setup Recommendations:
• HIGH Confidence (Score 75+): Use conservative strike selection
• MEDIUM Confidence (60-74): Moderate strikes with balanced risk
• LOW Confidence (<60): Aggressive strikes, higher risk

⚠️ Disclaimer: This is not financial advice. Paper trade first.
```

## Score Interpretation

- **75+ (🟢 HIGH)**: Conservative strikes, 5% OTM short, 10% OTM long
- **60-74 (🟡 MEDIUM)**: Moderate strikes, 8% OTM short, 13% OTM long  
- **< 60 (🔴 LOW)**: Aggressive strikes, 12% OTM short, 17% OTM long

## Scoring Components

The PCS score (0-100) is calculated from:

1. **RSI Analysis (30%)**: Optimal range for PCS is 30-75
2. **ADX Trend Strength (25%)**: Minimum 20 for strong trend
3. **Moving Average Support (20%)**: Price above SMA20 > SMA50
4. **Volume Analysis (15%)**: Current volume > 1.2x average
5. **MACD Momentum (10%)**: MACD above signal line

## Troubleshooting

### "Telegram credentials not configured"
- Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` environment variables
- Check spelling and that token/ID are correct (no extra spaces)

### "No high-probability setups found"
- Lower `DEFAULT_MIN_SCORE` to capture more stocks
- Check if market traded (weekends/holidays)
- Adjust RSI range or ADX minimum

### Network errors
- Check internet connection
- Verify proxy settings if behind corporate firewall
- Wait a few minutes for yfinance rate limits to reset

### Poor data quality
- Script requires minimum 20 days of price data
- Newer stocks may not have sufficient history
- Try running with `DEFAULT_MIN_SCORE = 45` for initial results

## Data Sources

- **Price Data**: Yahoo Finance (yfinance)
- **Technical Indicators**: TA-Lib (TALIB)
- **Update Frequency**: Real-time during market hours

## Important Disclaimers

⚠️ **This is NOT financial advice**
- Results are for educational purposes only
- Always paper trade before live trading
- Options trading involves substantial risk
- Past performance ≠ future results
- Consult qualified financial advisors

## Support & Feedback

Issues or improvements? Check the main README.md or open a GitHub issue.

---

**Happy Trading! 📈**
