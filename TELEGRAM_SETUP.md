# NSE F&O PCS Scanner - Telegram Setup Guide

## Overview
The `run_scanner.py` script analyzes NSE F&O stocks for Put Credit Spread opportunities and can send results directly to your Telegram account.

## How to Get Telegram Credentials

### Step 1: Create a Telegram Bot
1. Open Telegram and search for **@BotFather**
2. Send `/start` and then `/newbot`
3. Follow the prompts:
   - Choose a bot name (e.g., "NSE PCS Scanner Bot")
   - Choose a username (e.g., "nse_pcs_bot")
4. **BotFather** will provide your **Bot Token** (looks like: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)
5. Copy and save this token

### Step 2: Get Your Chat ID
1. In Telegram, start a chat with your new bot (search for its username)
2. Send `/start` to your bot
3. Open this URL in your browser: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Replace `<YOUR_BOT_TOKEN>` with your actual token
4. Look for `"chat": {"id": XXXXXXXX}` - that's your **Chat ID**
5. Copy and save this number

## Running the Scanner with Telegram

### Option 1: Set Environment Variables (Recommended for Automation)

**Linux/Mac:**
```bash
export TELEGRAM_BOT_TOKEN='your_bot_token_here'
export TELEGRAM_CHAT_ID='your_chat_id_here'
python3 run_scanner.py
```

**Windows (PowerShell):**
```powershell
$env:TELEGRAM_BOT_TOKEN='your_bot_token_here'
$env:TELEGRAM_CHAT_ID='your_chat_id_here'
python3 run_scanner.py
```

### Option 2: Create a .env File (Security Best Practice)

Create a file named `.env` in the repository root:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

Then modify `run_scanner.py` to load from .env:
```python
from dotenv import load_dotenv
load_dotenv()
```

Install python-dotenv:
```bash
pip install python-dotenv
```

### Option 3: Set in Scheduled Task Configuration

If you're using a scheduled task runner, add the environment variables to your task configuration.

## Output Format

When the scanner runs, it will:

1. **Scan** 25+ NSE F&O stocks
2. **Calculate** PCS scores (0-100) based on:
   - Trend strength
   - RSI momentum
   - MACD alignment
   - ADX strength
   - Volume confirmation
3. **Filter** for stocks scoring 55+ (configurable)
4. **Send** to Telegram with:
   - Stock symbol
   - PCS score and confidence level
   - Current price
   - Technical indicators
   - SMA20 level

### Example Telegram Message:

```
🚀 NSE F&O PCS Scan Results
📅 2026-08-03 09:12:58 IST
━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. RELIANCE
   Score: 78/100 HIGH ✅
   Price: ₹2945.50
   RSI: 58.3 | ADX: 28.5
   SMA20: ₹2920.00

2. HDFCBANK
   Score: 72/100 HIGH ✅
   Price: ₹1684.25
   ...

⚠️ Always verify before trading
#NSE #FO #Trading
```

## Customizing the Scanner

Edit these variables in `run_scanner.py`:

```python
DEFAULT_MIN_PCS_SCORE = 55         # Minimum score to report
MAX_STOCKS_TO_SCAN = 25            # Max stocks to analyze
MIN_VOLUME_RATIO = 1.2             # Min volume ratio vs average
```

## Scheduling the Scanner

### Using cron (Linux/Mac):

```bash
# Edit crontab
crontab -e

# Run scanner daily at 9:30 AM IST (after market open)
30 9 * * 1-5 cd /home/user/nsepcs && TELEGRAM_BOT_TOKEN='xxx' TELEGRAM_CHAT_ID='yyy' python3 run_scanner.py
```

### Using Task Scheduler (Windows):

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger to your preferred time
4. Set action to: `python3 C:\path\to\run_scanner.py`
5. In advanced options, set environment variables

### Using Claude Code Scheduled Task:

The script is configured to run as a scheduled task. Set the environment variables:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

## Troubleshooting

### "Telegram credentials not found"
- Ensure both `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set
- Check for typos in the token and chat ID

### "Network connectivity issue detected"
- The scanner automatically falls back to demonstration data
- This is expected in restricted network environments
- When network access is available, it will use live market data

### "Telegram API error: 403"
- Verify your bot token is correct
- Check that the bot hasn't been blocked or deleted

### "Connection tunnel failed"
- Network proxy may be blocking external connections
- Try running from a different network or environment

## Security Notes

⚠️ **Never hardcode credentials in scripts or commit them to git**

Best practices:
1. Use environment variables
2. Use `.env` files (add to `.gitignore`)
3. Use secrets management (GitHub Secrets, AWS Secrets Manager, etc.)
4. Rotate tokens periodically
5. Restrict bot permissions to "Send Messages" only

## What the Scanner Analyzes

### Technical Indicators (30% weight)
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- ADX (Average Directional Index)
- Bollinger Bands
- Moving Averages (SMA20, SMA50)

### Risk Management
- Volume confirmation
- Liquidity tiers
- Price proximity to support/resistance
- Trend strength validation

### F&O Stocks Covered
Tier 1: NIFTY, BANKNIFTY, RELIANCE, TCS, HDFCBANK, INFY, ICICIBANK, SBIN, LT, ITC

Tier 2: KOTAKBANK, AXISBANK, HCLTECH, WIPRO, MARUTI, ASIANPAINT, BHARTIARTL, SUNPHARMA, TATAMOTORS, ADANIENT

Tier 3: BAJFINANCE, BAJAJFINSV, INDUSINDBK, TECHM, TITAN, NESTLEIND, ULTRACEMCO, POWERGRID, NTPC, and others

## Disclaimer

⚠️ **This scanner is for educational purposes only. Always verify results independently before trading.**

- Past performance doesn't guarantee future results
- Options trading involves substantial risk
- Always use proper risk management and position sizing
- Never risk more than you can afford to lose
- Consult qualified financial advisors before making trading decisions

## Support

For issues or feature requests, check the main README.md or raise an issue in the repository.
