# NSE PCS Scanner - Telegram Integration Guide

## Overview
This guide shows you how to run the NSE PCS Scanner and send results to Telegram.

## Prerequisites
1. Python 3.8 or higher
2. Telegram account
3. Your telegram bot token and chat ID

## Step 1: Get Telegram Credentials

### Create a Telegram Bot
1. Open Telegram and search for `@BotFather`
2. Send `/start` and follow the instructions
3. Send `/newbot`
4. Follow the prompts to create your bot
5. **Save the bot token** (looks like: `123456789:ABCDEFGhijklmnopqrstuvwxyz`)

### Get Your Chat ID
1. Open Telegram and search for `@userinfobot`
2. Send `/start` and it will show your chat ID (looks like: `987654321`)

## Step 2: Install Dependencies

```bash
cd /home/user/nsepcs

# Install required packages
pip install -r requirements.txt

# If 'ta' package fails, install ta-lib instead:
pip install ta-lib
```

## Step 3: Run the Scanner

### Option A: Simple Mode (Display Results)
```bash
python run_scanner.py --stocks 50
```

### Option B: With Telegram Integration
```bash
python run_scanner.py \
  --stocks 100 \
  --telegram YOUR_BOT_TOKEN YOUR_CHAT_ID
```

**Example:**
```bash
python run_scanner.py \
  --stocks 100 \
  --telegram "123456789:ABCDEFGhijklmnopqrstuvwxyz" "987654321"
```

### Advanced Options
```bash
python run_scanner.py \
  --stocks 219 \
  --min-volume 1.2 \
  --min-strength 65 \
  --telegram "TOKEN" "CHAT_ID"
```

## Step 4: Results

### CSV Output
Results are automatically saved to:
```
/tmp/scan_results_YYYYMMDD_HHMMSS.csv
```

### Telegram Output
If Telegram is configured, you'll receive:
1. **Summary** - Total stocks found, average pattern strength
2. **Top Stocks** - Top 15 stocks with prices and metrics
3. **Full List** - All stock symbols found

## Streamlit Web Interface (Alternative)

### Run the Web App Locally
```bash
streamlit run streamlit_app.py
```

This opens the full professional UI where you can:
- Adjust filters interactively
- View detailed analysis for each stock
- Generate charts
- Export results

## File Descriptions

### Main Scripts
- **run_scanner.py** - Standalone CLI scanner with Telegram support
- **streamlit_app.py** - Full web interface (requires network access)
- **send_to_telegram.py** - Simple utility to send CSV results to Telegram

### Data Files
- **requirements.txt** - Python dependencies
- **TELEGRAM_SETUP.md** - This file

## Troubleshooting

### "Bot token invalid"
- Check that you've copied the full token including the colon
- Make sure you didn't add spaces

### "Chat ID invalid"
- Verify you got the correct chat ID from @userinfobot
- Chat IDs are numeric only

### "No stocks found"
- Lower the `--min-strength` value (try 50)
- Lower the `--min-volume` value (try 1.0)
- The scanner runs on closing day, so run during market hours

### Module import errors
- Make sure you've run: `pip install -r requirements.txt`
- For 'ta' issues: `pip install ta-lib`

## Example: Full Setup

```bash
# 1. Clone/navigate to project
cd /home/user/nsepcs

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run scanner and send to Telegram
python run_scanner.py \
  --stocks 219 \
  --min-volume 1.2 \
  --min-strength 65 \
  --telegram "YOUR_BOT_TOKEN" "YOUR_CHAT_ID"
```

## Automation

### Schedule Daily Scans (Linux/Mac)

Add to crontab:
```bash
# Run scanner every weekday at 3:30 PM IST
30 15 * * 1-5 cd /home/user/nsepcs && python run_scanner.py --stocks 219 --telegram "TOKEN" "CHAT_ID"
```

### Windows Scheduler
Use Task Scheduler to run:
```
python run_scanner.py --stocks 219 --telegram "TOKEN" "CHAT_ID"
```

## Support

For issues or questions about the scanner, check:
1. Stock symbols are correct (NSE format with .NS)
2. Network connection is available
3. Telegram bot token and chat ID are correct
4. Sufficient historical data exists (3 months minimum)

---

**Ready to start?** Provide your Telegram credentials and run the scanner locally!
