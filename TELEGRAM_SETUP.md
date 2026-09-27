# NSE F&O PCS Scanner - Telegram Integration Setup

## Overview
The `telegram_scanner.py` script runs a stock screening analysis for NSE F&O put credit spreads and sends the results directly to your Telegram chat.

## Features
- 🔍 Scans 34 NSE F&O stocks for optimal PCS opportunities
- 📊 Calculates PCS Score (0-100) based on 5 technical factors:
  - Bullish Momentum (RSI analysis) - 30%
  - Trend Strength (MACD) - 25%
  - Support Proximity - 20%
  - Volatility Optimization - 15%
  - Volume Confirmation - 10%
- ⚡ Filters stocks meeting minimum score threshold (default: 55)
- 📱 Sends formatted results directly to Telegram
- 🔄 Automatically uses synthetic data if real market data unavailable

## Setup Instructions

### Step 1: Create a Telegram Bot
1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow prompts to name your bot
4. You'll receive a **Bot Token** (looks like: `123456789:ABCdefGHIjklmnoPQRstuvwxyz`)
5. Save this token - you'll need it later

### Step 2: Get Your Chat ID
1. Search for `@userinfobot` on Telegram
2. Send `/start` command
3. It will show your **User ID** (numeric, e.g., `123456789`)
4. Alternatively, you can use a Telegram group ID

### Step 3: Configure Environment Variables
Set the following environment variables before running the scanner:

```bash
export TELEGRAM_BOT_TOKEN='123456789:ABCdefGHIjklmnoPQRstuvwxyz'
export TELEGRAM_CHAT_ID='123456789'
```

### Step 4: Run the Scanner
```bash
cd /home/user/nsepcs
python telegram_scanner.py
```

## Usage

### Command Line
```bash
python telegram_scanner.py
```

### Output
The script will:
1. Scan all 34 NSE F&O stocks
2. Calculate PCS scores for each
3. Filter stocks scoring ≥ 55
4. Send results to your Telegram chat
5. Show 10 top stocks in the message

### Example Output
```
🔍 NSE F&O PCS Scan Results
Found 29 stocks meeting filter criteria (PCS Score ≥ 55)
Scan time: 2026-09-27 03:43 UTC

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. RELIANCE
PCS Score: 100/100 🟢 HIGH
Price: ₹3850.25
RSI: 58.3
Volatility: 9.4%

... and 19 more stocks
```

## Configuration

### Minimum PCS Score
To adjust the filter threshold, edit `telegram_scanner.py`:
```python
results = scanner.scan_stocks(min_score=60)  # Change 55 to desired threshold
```

### Number of Stocks
To change the number of stocks returned:
```python
for i, result in enumerate(results[:15], 1):  # Change 10 to desired count
```

## Scheduled Execution

### Using cron (Linux/Mac)
Add to crontab:
```bash
# Run daily at 9:30 AM IST (04:00 UTC)
0 4 * * 1-5 export TELEGRAM_BOT_TOKEN='your_token' && export TELEGRAM_CHAT_ID='your_id' && cd /home/user/nsepcs && python telegram_scanner.py
```

### Using at (One-time execution)
```bash
export TELEGRAM_BOT_TOKEN='your_token'
export TELEGRAM_CHAT_ID='your_id'
at 09:30 AM tomorrow << 'EOF'
cd /home/user/nsepcs && python telegram_scanner.py
EOF
```

## Troubleshooting

### Bot Not Responding
1. Check bot token is correct
2. Verify chat ID is correct
3. Ensure bot has permission to message the chat
4. Check internet connectivity

### Network Errors
- Script automatically falls back to synthetic data if real data unavailable
- Message will show `⚠️ Data: Demo/Synthetic` indicator

### No Stocks Found
- This is normal on volatile market days
- Try lowering the `min_score` threshold
- Check market trading hours (Mon-Fri, 9:15 AM - 3:30 PM IST)

## Technical Details

### Data Sources
1. **Primary**: Yahoo Finance (real-time market data)
2. **Fallback**: Synthetic data generation (when network unavailable)

### Indicators Calculated
- RSI (14-period)
- SMA (20 and 50-period)
- EMA (20-period)
- Bollinger Bands (20-period, 2 std dev)
- MACD (12, 26, 9)

### Stocks Scanned
**Tier 1 (Ultra High Liquidity)**: NIFTY, BANKNIFTY, RELIANCE, TCS, HDFCBANK, INFY, ICICIBANK, SBIN, LT, ITC

**Tier 2 (High Liquidity)**: KOTAKBANK, AXISBANK, HCLTECH, WIPRO, MARUTI, ASIANPAINT, BHARTIARTL, SUNPHARMA, TATAMOTORS, ADANIENT

**Tier 3 (Medium Liquidity)**: BAJFINANCE, BAJAJFINSV, INDUSINDBK, TECHM, TITAN, NESTLEIND, ULTRACEMCO, POWERGRID, NTPC, ONGC, COALINDIA, JSWSTEEL, TATASTEEL, HINDALCO

## Performance
- Typical scan time: 30-90 seconds (depends on network)
- Results cached for 5 minutes
- Supports parallel processing (5 concurrent stock analyses)

## Disclaimer
⚠️ **This tool is for educational purposes only.** 
- Not financial advice
- Always verify data before trading
- Past performance ≠ future results
- Start with paper trading
- Consult qualified financial advisors

## Support
For issues or feature requests, check:
1. This documentation
2. GitHub issues
3. Application logs (console output)

---
**Last Updated**: 2026-09-27  
**Version**: 1.0
