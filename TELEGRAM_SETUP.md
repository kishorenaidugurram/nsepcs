# NSE PCS Scanner - Telegram Integration Setup

## Overview

The scanner runs technical analysis on NSE F&O stocks and sends qualifying results to Telegram.

## Setup Instructions

### 1. Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/start` and then `/newbot`
3. Follow the prompts to create your bot:
   - Give it a name (e.g., "NSE PCS Scanner")
   - Give it a username (e.g., "nse_pcs_bot")
4. BotFather will give you a **BOT_TOKEN** - save this

### 2. Get Your Telegram Chat ID

1. Search for and start **@userinfobot** in Telegram
2. It will show you your Telegram **User ID**
3. Start a chat with your bot (search for the bot username you created)
4. Send any message to the bot

The User ID from step 2 is your **CHAT_ID**

### 3. Set Environment Variables

Add these to your shell profile (~/.bashrc or ~/.zshrc):

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

Then run:
```bash
source ~/.bashrc
```

### 4. Run the Scanner

```bash
cd /home/user/nsepcs
python3 run_scanner_simple.py
```

## Usage

### Manual Scan
```bash
python3 run_scanner_simple.py
```

### Scheduled Scans (Cron)

Add to crontab (`crontab -e`):

```bash
# Run scanner daily at 3:30 PM IST (before market close at 3:30 PM)
30 15 * * 1-5 cd /home/user/nsepcs && python3 run_scanner_simple.py

# Run scanner weekly on Friday at 4:00 PM
0 16 * * 5 cd /home/user/nsepcs && python3 run_scanner_simple.py
```

## How It Works

1. **Scans** up to 50 NSE F&O stocks
2. **Analyzes** technical patterns:
   - Volume surges (>1.5x average)
   - Price breakouts above resistance
   - RSI levels (30-80 range)
   - ADX trend strength (>15)
3. **Filters** stocks with pattern strength >= 65%
4. **Sends** top 15 qualifying stocks to Telegram

## Output

Each Telegram message includes:
- Stock symbol
- Current price
- Technical indicators (RSI, ADX)
- Volume ratio
- Pattern strength %
- Confidence level

## Results Storage

Scan results are automatically saved as JSON:
```
/tmp/pcs_results_YYYYMMDD_HHMMSS.json
```

## Troubleshooting

### "No stocks found"
- Market might be closed
- All stocks may be below strength threshold (try lowering it)
- Network issues accessing data

### "Telegram credentials not configured"
- Check environment variables:
  ```bash
  echo $TELEGRAM_BOT_TOKEN
  echo $TELEGRAM_CHAT_ID
  ```
- If empty, re-run the setup steps above

### Connection errors
- Check network connectivity: `curl -s https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe`
- Verify proxy settings if in restricted environment

## Files

- `run_scanner_simple.py` - Main scanner (simplified, no heavy dependencies)
- `run_scanner_telegram.py` - Advanced scanner (needs ta library)
- `streamlit_app.py` - Full Streamlit web application

## Important Notes

⚠️ **Disclaimer:**
- Use this for research/education purposes only
- Past performance does not guarantee future results
- Always verify signals before trading
- Start with paper trading
- Never risk more than you can afford to lose

## Support

For issues or questions:
1. Check the logs in scanner output
2. Verify environment variables
3. Test network connectivity to APIs
4. Review the technical settings in the script
