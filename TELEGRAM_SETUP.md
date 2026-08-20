# Telegram Integration Setup Guide

This guide explains how to set up Telegram notifications for the NSE F&O PCS Scanner automated analysis.

## Overview

The scanner can automatically run analysis and send results to your Telegram chat. This requires:
1. A Telegram Bot Token (from BotFather)
2. Your Telegram Chat ID
3. Setting environment variables for the scheduled task

## Step 1: Create a Telegram Bot

### 1.1 Open Telegram and find BotFather
- Search for **@BotFather** in Telegram
- Start a chat with BotFather

### 1.2 Create a new bot
- Send the message: `/newbot`
- Follow the prompts:
  - Enter a name for your bot (e.g., "NSE PCS Scanner")
  - Enter a username for your bot (e.g., "nse_pcs_scanner_bot")
- **Save the bot token** - you'll need this in Step 3

Example token format: `123456789:ABCdefGHIjklmnoPQRstuvWXYZ`

## Step 2: Get Your Telegram Chat ID

### 2.1 Find @userinfobot
- Search for **@userinfobot** in Telegram
- Start a chat with it

### 2.2 Get your chat ID
- Send any message to @userinfobot
- It will reply with your User ID
- **Save this number** - you'll need it in Step 3

Example chat ID: `123456789`

## Step 3: Configure Environment Variables

Set the following environment variables for your scheduled task:

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

### Option A: Persistent Environment Variables (Recommended)

Add to your shell profile (`~/.bashrc`, `~/.zshrc`, or similar):

```bash
# NSE PCS Scanner Telegram Configuration
export TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklmnoPQRstuvWXYZ"
export TELEGRAM_CHAT_ID="123456789"
```

Then reload: `source ~/.bashrc`

### Option B: Using a .env file

Create `/home/user/nsepcs/.env`:

```bash
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklmnoPQRstuvWXYZ
TELEGRAM_CHAT_ID=123456789
```

Then load before running the script:
```bash
source /home/user/nsepcs/.env
python run_with_sample_data.py
```

## Step 4: Run the Analysis Script

### With Real-Time Data (Requires Network Access)

```bash
python run_simplified_analysis.py
```

This will:
1. Fetch live stock data from Yahoo Finance
2. Analyze 30 stocks based on PCS criteria
3. Filter stocks with PCS score ≥ 60
4. Send results to Telegram
5. Save results to CSV

### With Sample Data (No Network Required)

```bash
python run_with_sample_data.py
```

This will:
1. Use representative sample data
2. Demonstrate the Telegram notification format
3. Save example results to CSV
4. Work offline (useful for testing)

## Step 5: Automate with Cron (Linux/Mac)

To run the analysis automatically on a schedule:

```bash
# Edit crontab
crontab -e

# Example: Run daily at 9:30 AM IST (4:00 AM UTC)
0 4 * * * source ~/.bashrc && cd /home/user/nsepcs && python run_simplified_analysis.py >> logs/pcs_scan.log 2>&1
```

## Troubleshooting

### Issue: "Telegram credentials not configured"
**Solution:** Ensure `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set as environment variables.

```bash
# Verify they're set:
echo $TELEGRAM_BOT_TOKEN
echo $TELEGRAM_CHAT_ID
```

### Issue: "Network connection failed" or "403 Forbidden"
**Solution:** Yahoo Finance access is blocked by the proxy. 
- Use `run_with_sample_data.py` instead for offline testing
- Contact network admin to allowlist `query.yahooapis.com` and `fc.yahoo.com`

### Issue: "Invalid bot token"
**Solution:** Check that your bot token is correct. It should be in format: `123456789:ABCdefGHIjklmnoPQRstuvWXYZ`

### Issue: Message not received
**Solutions:**
1. Verify your chat ID is correct (should be numeric)
2. Ensure the bot can message you (you should have started a chat with the bot first)
3. Check Telegram's privacy settings if using a group chat

## Message Format

The Telegram message includes:

```
📊 NSE F&O PCS Scanner Results
_2026-08-20 03:42 IST_

✅ Found 7 stocks (Score ≥ 60)
──────────────────────────────

1. RELIANCE 🟢
   Score: 78.5 | Price: ₹2845.50
   RSI: 48.2 | Vol: 1.8x
   📌 Strong uptrend

2. TCS 🟡
   Score: 72.3 | Price: ₹3680.25
   ...
```

**Legend:**
- 🟢 GREEN = HIGH confidence (Score 75+)
- 🟡 YELLOW = MEDIUM confidence (Score 60-74)
- 🔴 RED = LOW confidence (Score <60)

## Supported Stock Universe

The scanner analyzes 30 stocks across 3 liquidity tiers:

**Tier 1 (Ultra High Liquidity):**
- RELIANCE, TCS, HDFCBANK, INFY, ICICIBANK, SBIN, LT, ITC

**Tier 2 (High Liquidity):**
- KOTAKBANK, AXISBANK, HCLTECH, WIPRO, MARUTI, ASIANPAINT, BHARTIARTL, SUNPHARMA

**Tier 3 (Medium Liquidity):**
- BAJFINANCE, BAJAJFINSV, INDUSINDBK, TECHM, TITAN, NESTLEIND, ULTRACEMCO, POWERGRID, NTPC, ONGC, COALINDIA, JSWSTEEL, TATASTEEL, HINDALCO

## PCS Score Components

The scanner evaluates each stock on 5 dimensions:

1. **Momentum (30%)** - RSI analysis
2. **Trend Strength (25%)** - MACD, EMA, SMA analysis
3. **Support Proximity (20%)** - Distance from key moving averages
4. **Volume Confirmation (10%)** - Volume ratio to 20-day average
5. **Volatility Assessment (15%)** - Annualized volatility analysis

## Support & Documentation

For more information:
- README.md - Project overview and features
- streamlit_app.py - Full application with interactive UI
- run_simplified_analysis.py - Command-line script for real-time analysis
- run_with_sample_data.py - Demo script with sample data

## Disclaimer

⚠️ **IMPORTANT:** This tool is for educational and analysis purposes only.
- Not financial advice
- Always verify results independently
- Consult a financial advisor before trading
- Test with paper trading first
- Past performance does not guarantee future results
