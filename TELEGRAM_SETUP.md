# Telegram Integration for PCS Scanner

This guide explains how to set up the NSE F&O PCS Screener to automatically send scan results to your Telegram account.

## Quick Start

### 1. Get Your Telegram Bot Token

1. Open Telegram and search for **@BotFather**
2. Send `/start` to begin
3. Send `/newbot` to create a new bot
4. Follow the prompts:
   - Give your bot a name (e.g., "PCS Scanner")
   - Give it a username (e.g., "@pcs_scanner_bot")
5. BotFather will provide you with a **TOKEN** - save this!

Example token format: `123456789:ABCdefGHIjklmnoPQRstuvWXYZ-1234567890`

### 2. Get Your Chat ID

1. Send a message to your new bot (message doesn't matter)
2. Visit this URL in your browser (replace TOKEN with your actual token):
   ```
   https://api.telegram.org/botTOKEN/getUpdates
   ```
3. Look for the `"chat"` object and find `"id"` - this is your **CHAT_ID**

Example chat ID format: `123456789`

### 3. Set Environment Variables

Set these environment variables to enable Telegram notifications:

**On Linux/Mac:**
```bash
export TELEGRAM_BOT_TOKEN='your_bot_token_here'
export TELEGRAM_CHAT_ID='your_chat_id_here'
```

**On Windows (PowerShell):**
```powershell
$env:TELEGRAM_BOT_TOKEN='your_bot_token_here'
$env:TELEGRAM_CHAT_ID='your_chat_id_here'
```

**For permanent setup, add to ~/.bashrc or ~/.profile:**
```bash
echo "export TELEGRAM_BOT_TOKEN='your_token'" >> ~/.bashrc
echo "export TELEGRAM_CHAT_ID='your_chat_id'" >> ~/.bashrc
source ~/.bashrc
```

## Using the Scanners

### Demo Scanner (with sample data)
```bash
python3 run_scan_demo.py
```

This demonstrates the full functionality without needing market data access.

### Live Scanner (with real market data)
```bash
python3 run_scan_simple.py
```

This scans real NSE F&O stocks using live market data.

### Full-Featured Scanner (original Streamlit app)
```bash
streamlit run streamlit_app.py
```

This runs the full web application with all features.

## Automation

To run the scanner automatically on a schedule, use cron (Linux/Mac) or Task Scheduler (Windows).

### Cron Example (every day at 3:30 PM IST):
```bash
30 15 * * * cd /home/user/nsepcs && /usr/local/bin/python3 run_scan_simple.py >> /var/log/pcs_scan.log 2>&1
```

### Cron Example (every weekday at market open):
```bash
0 9 * * 1-5 cd /home/user/nsepcs && /usr/local/bin/python3 run_scan_simple.py >> /var/log/pcs_scan.log 2>&1
```

## Testing Your Setup

Run this to verify your Telegram credentials are working:

```bash
python3 -c "
import os
import requests
token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')
if token and chat_id:
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    payload = {'chat_id': chat_id, 'text': '🤖 PCS Scanner is ready!'}
    requests.post(url, json=payload)
    print('✅ Test message sent successfully!')
else:
    print('❌ Telegram credentials not set')
"
```

## Filter Customization

The scanners use default filters for basic screening. You can customize these in the script:

- **RSI Range**: 30-75 (sweet spot: 45-65)
- **ADX Minimum**: 20 (trend strength)
- **Volume Ratio**: 1.2x (above-average volume)
- **Pattern Strength**: 65+ (confidence threshold)

Edit these in `run_scan_simple.py` in the `analyze_stock()` function.

## Output

Results are saved to:
- **JSON**: `/tmp/pcs_scan_results.json`
- **Terminal**: Printed to stdout
- **Telegram**: Sent to your configured chat (if credentials set)

## Troubleshooting

### "Could not send to Telegram"
- Verify `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set correctly
- Test with the verification script above
- Check your internet connection

### "No stocks found"
- Verify market data is accessible
- Check if scanning too many stocks (reduce in script)
- Verify RSI/ADX thresholds aren't too strict

### "ModuleNotFoundError"
- Run: `pip install -r requirements.txt`
- For scanners: `pip install pandas numpy yfinance pytz requests`

## Best Practices

1. ✅ Test with demo scanner first
2. ✅ Use appropriate time filters (market hours)
3. ✅ Monitor first few scans before full automation
4. ✅ Keep bot token secret - never share it
5. ✅ Review results before trading
6. ✅ This is a screening tool, not trading advice

## Files

- `run_scan_demo.py` - Demo scanner with sample data
- `run_scan_simple.py` - Live scanner with real market data
- `run_pcs_scan.py` - Advanced scanner with full feature set
- `streamlit_app.py` - Full web application
- `TELEGRAM_SETUP.md` - This file

## Support

For issues or questions:
1. Check the logs in `/var/log/pcs_scan.log` (if automated)
2. Run the demo scanner to verify setup
3. Review the API documentation at https://core.telegram.org/bots/api
