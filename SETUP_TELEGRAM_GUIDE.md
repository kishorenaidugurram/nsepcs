# NSE Stock Scanner - Telegram Setup Guide

## Overview
This guide will help you set up the stock scanner to run on your local machine and send results to Telegram.

## Prerequisites
- Python 3.9+ installed on your local machine
- Internet connection
- Telegram account
- ~5-10 minutes setup time

## Step 1: Create a Telegram Bot

### 1.1 Open Telegram and search for @BotFather
1. Open Telegram app or web version
2. Search for `@BotFather` (official Telegram bot manager)
3. Click on it and start the chat

### 1.2 Create a new bot
1. Send message: `/newbot`
2. BotFather will ask for a name (e.g., "NSE Stock Scanner")
3. Choose a unique username (e.g., "nse_stock_scanner_bot")
4. BotFather will provide your `BOT_TOKEN`

**Save this BOT_TOKEN - you'll need it later!**

Example token looks like: `1234567890:ABCdefGHIjklmnOPqrsTUVwxyz-1234567`

## Step 2: Get Your Telegram Chat ID

### Method 1: Using @userinfobot
1. Search for `@userinfobot` in Telegram
2. Start a chat with it
3. It will show your User ID/Chat ID

**Save this CHAT_ID - usually starts with a hyphen for groups**

### Method 2: Manual method
1. Start a chat with your bot (send any message)
2. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Replace `<YOUR_BOT_TOKEN>` with your actual token
4. Look for "chat":{"id": in the response

## Step 3: Set Up Your Local Machine

### 3.1 Clone or download the repository
```bash
# Navigate to your project directory
cd /path/to/nsepcs
```

### 3.2 Install dependencies
```bash
# Install required Python packages
pip install -r requirements.txt

# If 'ta' package fails to install, use this alternative:
pip install TA-Lib yfinance pandas numpy plotly pytz beautifulsoup4 openpyxl
```

### 3.3 Set environment variables

#### On Windows (PowerShell):
```powershell
$env:TELEGRAM_BOT_TOKEN = "your_bot_token_here"
$env:TELEGRAM_CHAT_ID = "your_chat_id_here"
```

#### On Windows (Command Prompt):
```cmd
set TELEGRAM_BOT_TOKEN=your_bot_token_here
set TELEGRAM_CHAT_ID=your_chat_id_here
```

#### On macOS/Linux:
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

#### Permanent setup (macOS/Linux):
Add to your `~/.bashrc` or `~/.zshrc`:
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

Then run:
```bash
source ~/.bashrc  # or source ~/.zshrc
```

## Step 4: Run the Scanner

### Option A: Simple Scanner (Recommended for beginners)
```bash
python3 simple_scanner.py
```

This will:
1. Scan all F&O stocks for breakouts
2. Display results in your terminal
3. Save results to a CSV file
4. Send top 10 results to Telegram

### Option B: Full Telegram Scanner
```bash
python3 telegram_scanner.py
```

This uses more advanced filters and sends detailed Telegram messages.

### Option C: Original Streamlit App
```bash
streamlit run streamlit_app.py
```

This opens a web interface (http://localhost:8501)

## Step 5: Automate Scanning (Optional)

### Windows - Task Scheduler
1. Open Task Scheduler
2. Create a new basic task
3. Set trigger to daily at specific time (e.g., 3:45 PM)
4. Action: Start program
5. Program: `python.exe`
6. Arguments: `C:\path\to\simple_scanner.py`
7. Add environment variables before running

### macOS/Linux - Cron Job
1. Open terminal
2. Run: `crontab -e`
3. Add a line (runs at 3:45 PM every trading day):
```bash
45 15 * * 1-5 cd /path/to/nsepcs && /usr/bin/python3 simple_scanner.py
```

4. Save and close

## Telegram Bot Commands

Once your bot is set up, you can:

1. **Send text messages to the bot:**
   - The bot will respond with scan results
   - Send any message to get the latest scan

2. **Receive automatic updates:**
   - The scanner sends results automatically when run

3. **Stop receiving messages:**
   - Just block the bot or delete the chat

## Troubleshooting

### Problem: Bot not responding to messages
**Solution:** 
- Make sure you sent the bot at least one message first
- Check BOT_TOKEN is correct
- Try @BotFather > /token > select your bot to get token again

### Problem: Getting 403 errors
**Solution:**
- Check your CHAT_ID - should be numeric or -numeric for groups
- Make sure BOT_TOKEN is complete and hasn't been regenerated

### Problem: "No stocks found matching criteria"
**Solution:**
- This is normal during low volatility days
- Check if the market is open (NSE open 9:15 AM - 3:30 PM IST)
- Try adjusting filter criteria in the script

### Problem: Python module not found errors
**Solution:**
- Run: `pip install --upgrade pip`
- Run: `pip install -r requirements.txt` again
- If 'ta' fails, use: `pip install TA-Lib`

### Problem: Network/SSL errors
**Solution:**
- Update CA certificates: `pip install --upgrade certifi`
- Use: `export REQUESTS_CA_BUNDLE=/path/to/ca-bundle.crt`

## File Structure

```
nsepcs/
├── simple_scanner.py          # Simplified scanner (recommended)
├── telegram_scanner.py        # Full-featured Telegram integration
├── streamlit_app.py           # Web UI version
├── run_scanner.py             # CLI standalone runner
├── requirements.txt           # Python dependencies
└── SETUP_TELEGRAM_GUIDE.md    # This file
```

## Scanner Filters (Default Settings)

### Volume Criteria
- Current volume must be ≥ 1.2x of 20-day average

### Technical Criteria
- RSI: 30-75 (oversold to overbought)
- ADX: ≥ 20 (trend strength)
- Pattern: Current day breakout with tight consolidation

### Results
- Only stocks with current day breakout detected
- Sorted by breakout strength (highest first)
- Top 20 stocks displayed

## Customizing the Scanner

### Edit Filter Criteria
In `simple_scanner.py`, find the `scan_stocks()` function:

```python
if volume_ratio < 1.2:  # Change to adjust volume filter
    continue

if current_rsi > 75 or current_rsi < 30:  # Adjust RSI limits
    continue

if current_adx < 20:  # Change ADX minimum
    continue
```

### Change Stock Universe
```python
# To scan fewer stocks for faster results
results = scan_stocks(COMPLETE_NSE_FO_UNIVERSE[:50])  # Only first 50
```

## Support & Issues

If you encounter issues:
1. Check the logs in the output
2. Verify Telegram credentials are correct
3. Ensure Python 3.9+ is installed
4. Check internet connection
5. For library issues: `pip install --upgrade <package_name>`

## Legal Disclaimer

⚠️ **Important:**
- This tool is for educational and research purposes only
- Not financial advice - consult a financial advisor
- Past performance ≠ Future results
- Always do your own due diligence
- Options trading involves significant risk

## Next Steps

1. ✅ Create Telegram bot (Step 1-2)
2. ✅ Set environment variables (Step 3)
3. ✅ Run scanner locally (Step 4)
4. ✅ (Optional) Set up automation (Step 5)
5. 📊 Review results and adjust filters as needed

## Questions?

Common questions answered:
- **How often should I run the scan?** Daily after market close (3:45 PM IST) is ideal
- **Which stocks are scanned?** All 200+ NSE F&O liquid stocks
- **Can I add more stocks?** Yes, edit `COMPLETE_NSE_FO_UNIVERSE` list
- **Does it trade automatically?** No, it only sends alerts - you decide to trade
- **Is it free?** Yes, uses free APIs and Telegram is free
- **Works on mobile?** You can view results on mobile Telegram, but must run scanner on computer

---

**Ready to start?** Begin with Step 1: Create a Telegram Bot! ✅
