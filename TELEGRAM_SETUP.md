# Telegram Integration Setup Guide

This guide explains how to set up Telegram notifications for the NSE F&O PCS Screener.

## Quick Start

### 1. Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send the command `/start`
3. Send the command `/newbot`
4. Follow the prompts to create a bot
   - Give it a name (e.g., "NSE PCS Screener")
   - Give it a username (e.g., "nse_pcs_bot")
5. Copy the **HTTP API token** - this is your `TELEGRAM_BOT_TOKEN`

Example token format: `123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh`

### 2. Get Your Chat ID

1. Send a message to your newly created bot
2. Go to this URL in your browser (replace TOKEN with your bot token):
   ```
   https://api.telegram.org/bot{TOKEN}/getUpdates
   ```
3. Look for `"chat":{"id":` in the response
4. Copy the ID number - this is your `TELEGRAM_CHAT_ID`

Example: If you see `"id":1234567890`, your chat ID is `1234567890`

### 3. Configure Environment Variables

Copy the `.env.example` file:
```bash
cp .env.example .env
```

Edit `.env` and add your credentials:
```
TELEGRAM_BOT_TOKEN=123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh
TELEGRAM_CHAT_ID=1234567890
```

### 4. Verify Configuration

Test your configuration by running:
```bash
python3 standalone_analysis.py
```

You should see a message in your Telegram chat with scan results.

## Using with Streamlit

The main Streamlit app (`streamlit run streamlit_app.py`) is designed for interactive use. For automated scans with Telegram notifications, use the standalone script.

## Automation Options

### Option 1: Cron Job (Linux/Mac)

To run scans automatically every day at 9 AM IST:

1. Edit your crontab:
   ```bash
   crontab -e
   ```

2. Add this line (adjust path to your project):
   ```bash
   0 3 * * 1-5 cd /home/user/nsepcs && /usr/bin/python3 standalone_analysis.py >> /var/log/pcs_scan.log 2>&1
   ```

   Note: 3 UTC = 8:30 AM IST (adjust for your timezone)

3. Make sure to set environment variables in a wrapper script or `.bashrc`

### Option 2: GitHub Actions (if using GitHub)

Create `.github/workflows/daily-scan.yml`:

```yaml
name: Daily PCS Scan

on:
  schedule:
    - cron: '0 3 * * 1-5'  # 8:30 AM IST on weekdays
  workflow_dispatch:

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run PCS Scan
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: python3 standalone_analysis.py
```

### Option 3: Cloud Scheduler (Google Cloud, AWS, etc.)

Use your cloud provider's scheduler to trigger the script periodically.

## Results Format

The Telegram notification includes:

- 🎯 **Scan Results Header**
- 📅 Timestamp (IST)
- ✅ Total stocks found
- 🏆 **Top 10 opportunities** with:
  - Stock symbol
  - Current price
  - RSI indicator
  - ADX indicator
  - Composite score

## Troubleshooting

### No message received?

1. Verify your bot token is correct
2. Verify your chat ID is correct
3. Ensure the bot has permission to send messages (send any message to it first)
4. Check that TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables are set

### Connection error?

1. Check your internet connection
2. If behind a proxy, ensure it's properly configured
3. Try accessing `https://api.telegram.org/` in your browser to verify connectivity

### Script not running on schedule?

1. Check cron logs: `grep CRON /var/log/syslog`
2. Verify environment variables are loaded in cron context
3. Ensure the Python path in cron is correct

## Security Notes

- **Never commit `.env` file** to version control
- Add `.env` to `.gitignore`
- Use environment variables for production deployments
- Consider using a dedicated bot account per environment (dev, prod)

## Support

For issues with:
- **Telegram Bot Setup**: Contact [@BotFather](https://t.me/BotFather) on Telegram
- **Script Errors**: Check the log files
- **Streamlit App**: See main README.md

---

Happy trading! 📈
