# Telegram Scanner Setup Guide

## Overview
The NSE F&O PCS Scanner can automatically send stock analysis results to your Telegram chat. This guide walks you through setting up the scanner with Telegram notifications.

## Step 1: Create a Telegram Bot

1. **Open Telegram** and search for `@BotFather`
2. **Start a conversation** with BotFather by clicking `/start`
3. **Create a new bot** by sending `/newbot`
4. **Follow the prompts:**
   - Choose a name for your bot (e.g., "NSE Scanner Bot")
   - Choose a username for your bot (must end with `bot`, e.g., "nsepcs_bot")
5. **Copy the bot token** that BotFather provides (looks like: `123456789:ABCDefGHIjKLmnoPQRstUVwxYZ`)
   - This is your `TELEGRAM_BOT_TOKEN`

## Step 2: Get Your Chat ID

### Method 1: Using a Bot (Easiest)
1. Search for `@userinfobot` on Telegram
2. Click `/start` or send `/start` to the bot
3. The bot will show your user ID
   - This is your `TELEGRAM_CHAT_ID`

### Method 2: Manual Method
1. Message your newly created bot (the one you created in Step 1)
2. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Replace `<YOUR_BOT_TOKEN>` with your actual token
3. Look for `"id": <your_chat_id>` in the response
   - This is your `TELEGRAM_CHAT_ID`

## Step 3: Configure Environment Variables

### For Local Development
```bash
export TELEGRAM_BOT_TOKEN='123456789:ABCDefGHIjKLmnoPQRstUVwxYZ'
export TELEGRAM_CHAT_ID='987654321'

# Then run the scanner
python3 run_scanner_and_notify.py
```

### For Scheduled Execution (Cron)
Add to your crontab or scheduled task runner:

```bash
# Daily scan at 9:00 AM IST
0 9 * * * TELEGRAM_BOT_TOKEN='your_token_here' TELEGRAM_CHAT_ID='your_chat_id_here' python3 /path/to/run_scanner_and_notify.py

# Or run it every 4 hours
0 */4 * * * TELEGRAM_BOT_TOKEN='your_token_here' TELEGRAM_CHAT_ID='your_chat_id_here' python3 /path/to/run_scanner_and_notify.py
```

### For Cloud Environments (GitHub Actions, etc.)
Store as repository secrets or environment variables in your CI/CD configuration:

```yaml
- name: Run NSE Scanner
  env:
    TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
    TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
  run: python3 run_scanner_and_notify.py
```

## Step 4: Test the Setup

### Test Connection
```bash
# Set your credentials
export TELEGRAM_BOT_TOKEN='your_token'
export TELEGRAM_CHAT_ID='your_chat_id'

# Run a quick test
python3 run_scanner_and_notify.py
```

You should see:
1. Scanner starts analyzing stocks
2. Results are calculated
3. Message is sent to your Telegram chat

### Expected Telegram Message
You'll receive a message like:

```
📊 NSE F&O PCS Scanner Results
🕐 Time: 2026-08-21 10:30 IST
✨ Stocks Found: 15
⚠️ Failed: 193

1. RELIANCE     | PCS: 75 | RSI: 55 | ₹2850.50
2. HDFCBANK     | PCS: 72 | RSI: 48 | ₹1950.25
3. INFY         | PCS: 70 | RSI: 52 | ₹1620.00
...
```

## Troubleshooting

### "No Telegram credentials configured"
**Solution:** Make sure environment variables are set:
```bash
echo $TELEGRAM_BOT_TOKEN
echo $TELEGRAM_CHAT_ID
```

### "Failed to send message"
**Possible causes:**
1. Invalid bot token - verify the token format
2. Invalid chat ID - use @userinfobot to get correct ID
3. Network connectivity issues
4. Bot not added to chat - manually message the bot first

### "No stocks meeting filter criteria"
**Possible causes:**
1. Market conditions don't match the filter
2. Network connection issues (no data fetched)
3. RSI/ADX thresholds too strict
4. Try adjusting pattern_strength_min in the code

### "Connection timeout"
**Solution:** Check network connectivity and proxy settings. In restricted environments, the scanner will display results locally without sending to Telegram.

## Scanner Configuration

The scanner uses these default filters:
- **RSI Range:** 30-75
- **ADX Minimum:** 20
- **Volume Ratio:** 1.2x
- **MA Support:** ±3% from SMA(20)
- **Pattern Strength:** 65%+ minimum

To modify these, edit `run_scanner_and_notify.py`:
```python
config = {
    'rsi_min': 30,        # Change to adjust minimum RSI
    'rsi_max': 75,        # Change to adjust maximum RSI
    'adx_min': 20,        # Change to adjust minimum ADX
    'ma_support': True,   # Set to False to disable MA support check
    'ma_tolerance': 3,    # Change to adjust tolerance percentage
    'min_volume_ratio': 1.2,  # Change to adjust volume requirement
}
```

## Output Files

The scanner doesn't create output files by default. To add CSV export:
1. Modify the `format_message()` method
2. Add results export logic
3. Run after scanning completes

## Performance Notes

- **Scan Time:** ~60-120 seconds for 208 stocks
- **Data Period:** Last 3 months of price data
- **Technical Indicators:** Calculated for each stock
- **Network:** Requires internet access to fetch market data

## Security Best Practices

1. **Never commit credentials** to git
2. **Use GitHub Secrets** for CI/CD environments
3. **Rotate bot token** if accidentally exposed
4. **Use environment variables** for local development
5. **Keep credentials in** `.env` file (add to `.gitignore`)

## Support

For issues:
1. Check scanner logs for error messages
2. Verify Telegram bot token and chat ID
3. Test network connectivity
4. Check Python dependencies: `pip install -r requirements.txt`

## Next Steps

1. ✅ Create Telegram bot with @BotFather
2. ✅ Get your Chat ID
3. ✅ Set environment variables
4. ✅ Run the scanner
5. ✅ Set up scheduled execution (cron or CI/CD)

---
**Last Updated:** 2026-08-21
