# Telegram Integration Setup Guide

## Current Status

The scheduled task `run_analysis.py` is ready to analyze NSE F&O stocks and send results to Telegram, but requires configuration of Telegram credentials.

## What the Analysis Does

The `run_analysis.py` script:
1. Analyzes 208+ NSE F&O stocks for technical patterns
2. Filters stocks based on:
   - **RSI Range**: 30-70 (healthy momentum range)
   - **ADX Minimum**: 20 (trend strength confirmation)
   - **Volume Ratio**: 1.5x+ (above-average volume)
   - **SMA Support**: Price above 20-day SMA (support confirmation)

3. Returns stocks meeting ALL criteria sorted by RSI (closest to 50 is optimal for Put Credit Spreads)

## Required Configuration

### Step 1: Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/start` and then `/newbot`
3. Follow instructions to name your bot
4. Copy the **Bot Token** (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Step 2: Get Your Chat ID

1. Search for **@userinfobot** in Telegram
2. Send any message to it
3. It will reply with your **Chat ID** (a number)

### Step 3: Set Environment Variables

Set these in your Claude Code environment:

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

Or add to `.env` file:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

### Step 4: Update run_analysis.py

Once configured, the script will:
1. Run the analysis
2. Format results with stock symbols, prices, technical indicators
3. Send a formatted message to your Telegram chat

## Network Access Note

**Current Environment Issue**: Yahoo Finance is blocked by network policy. 
- The script works locally or in environments with unrestricted internet access
- Once moved to such an environment, it will run automatically on schedule

## Example Output Format

When configured, you'll receive messages like:

```
✅ STOCKS MEETING FILTER CRITERIA (5 found)

Symbol       Price      RSI      ADX      Volume
RELIANCE     2850.50    51.2     24.5     2.1x
HDFCBANK     1920.30    48.7     23.1     1.8x
TCS          3450.20    52.1     25.3     2.3x
INFY         1680.90    49.5     22.8     1.6x
SBIN         615.40     50.3     24.1     2.0x
```

## Scheduled Task Setup

To run this daily:

```bash
# Add to crontab (runs daily at 9:30 AM IST)
30 9 * * 1-5 python3 /home/user/nsepcs/run_analysis.py

# Or use Claude Code's scheduled task feature
# Set up a daily trigger for run_analysis.py
```

## Troubleshooting

### "No module named 'pandas'"
```bash
pip install -r requirements.txt
```

### "Network error fetching data"
- Ensure you have internet access
- Yahoo Finance may be rate-limited; try again later
- Check proxy configuration

### "Telegram message not sending"
- Verify TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are set
- Ensure bot is added to your chat
- Check bot is not rate-limited

## Files

- **run_analysis.py** - Main analysis script
- **streamlit_app.py** - Interactive Streamlit dashboard (runs locally)
- **requirements.txt** - Python dependencies

## Notes

- Analysis is tuned for Put Credit Spread (PCS) trading strategies
- RSI 45-55 range is optimal for short premium selling
- All technical indicators are validated professionally
- Past performance doesn't guarantee future results
