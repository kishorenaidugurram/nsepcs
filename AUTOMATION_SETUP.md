# NSE F&O PCS Screener - Automated Telegram Integration

## Overview

The NSE F&O PCS Screener can now be run automatically as a scheduled task and send results directly to your Telegram bot. This document explains how to set it up.

## Setup Instructions

### 1. Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/start` command
3. Send `/newbot` command
4. Choose a name for your bot (e.g., "NSE PCS Scanner")
5. Choose a username for your bot (must end with `bot`, e.g., "nse_pcs_bot")
6. BotFather will provide you with a **Bot Token** (looks like: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### 2. Get Your Chat ID

1. Open Telegram and search for **@userinfobot**
2. Send `/start` command
3. Your **Chat ID** will be displayed (a number like `987654321`)

### 3. Set Environment Variables

Set these environment variables on your system:

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

Or add them to your `.bashrc` or `.zshrc` file for permanent storage:

```bash
echo 'export TELEGRAM_BOT_TOKEN="your_bot_token_here"' >> ~/.bashrc
echo 'export TELEGRAM_CHAT_ID="your_chat_id_here"' >> ~/.bashrc
source ~/.bashrc
```

### 4. Run the Automated Scanner

```bash
python /home/user/nsepcs/run_scanner_simplified.py
```

## Features

### Filter Criteria (Default Settings)

The scanner uses these default filter criteria:

- **RSI Range**: 30-75 (optimal momentum conditions)
- **ADX Minimum**: 20 (trend strength indicator)
- **Volume Ratio**: 1.2x average (above-average volume)
- **Analysis Scope**: Top 50 NSE F&O stocks

### Output Format

The scanner produces:

1. **Console Output**: Summary of findings with top stocks
2. **JSON Results**: Detailed results in `scan_results.json`
3. **CSV Export**: Formatted report in `scan_results.csv`
4. **Telegram Message**: Formatted and sent to your Telegram bot

### Result Categories

Stocks are categorized by strength score:

- **🟢 High Strength (70-100%)**: Strongest signals, most likely to meet criteria
- **🟡 Medium Strength (50-70%)**: Moderate signals
- **🔴 Low Strength (<50%)**: Weaker signals

## Running on Schedule

### Option 1: Using Cron (Linux/Mac)

Edit your crontab:

```bash
crontab -e
```

Add a line to run the scanner daily at 4:00 PM IST:

```bash
0 16 * * * cd /home/user/nsepcs && python run_scanner_simplified.py >> /tmp/pcs_scanner.log 2>&1
```

Or every weekday at market close (3:30 PM IST):

```bash
30 15 * * 1-5 cd /home/user/nsepcs && python run_scanner_simplified.py >> /tmp/pcs_scanner.log 2>&1
```

### Option 2: Using Task Scheduler (Windows)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (daily, weekly, etc.)
4. Add action: `python C:\path\to\run_scanner_simplified.py`

### Option 3: Using Claude Code Scheduled Tasks

You can set up a recurring Claude Code session to run this automatically:

```bash
claude code
/loop 24h run_scanner_simplified.py
```

## File Structure

```
/home/user/nsepcs/
├── streamlit_app.py              # Main Streamlit application
├── run_scanner_simplified.py     # Automated scanner script (NO TA package required)
├── run_scanner.py                # Full-featured scanner (requires TA package)
├── scan_results.json             # Latest scan results (JSON format)
├── scan_results.csv              # Latest scan results (CSV format)
├── AUTOMATION_SETUP.md           # This file
└── README.md                      # Original documentation
```

## Sample Telegram Output

The scanner sends a formatted message like:

```
🎯 NSE F&O PCS Screener Results
📅 2026-09-08 16:30 IST

🟢 HIGH STRENGTH (5)
  • RELIANCE - ₹2,750.50 | Strength: 85%
  • TCS - ₹3,450.25 | Strength: 82%
  • HDFC - ₹2,150.75 | Strength: 78%
  • INFY - ₹1,850.00 | Strength: 76%
  • ICICI - ₹850.50 | Strength: 72%

🟡 MEDIUM STRENGTH (12)
  ... additional stocks ...

📊 Total Stocks Found: 17
```

## Troubleshooting

### No Telegram Message Sent?

Check that environment variables are set:

```bash
echo $TELEGRAM_BOT_TOKEN
echo $TELEGRAM_CHAT_ID
```

If empty, set them again and verify with:

```bash
env | grep TELEGRAM
```

### Network Connection Issues?

The script requires internet access to:
- Download stock data from Yahoo Finance
- Send messages to Telegram

If you're behind a corporate proxy:

1. Set proxy environment variables:
   ```bash
   export HTTP_PROXY="http://proxy.company.com:8080"
   export HTTPS_PROXY="http://proxy.company.com:8080"
   ```

2. Or modify the script to use a different data source

### No Stocks Found?

This can happen if:
1. Market is closed
2. Filter criteria are too strict
3. No stocks meet the technical criteria on that day

Adjust filter values in the script if needed.

## Performance Notes

- **Scan Time**: ~2-3 minutes for 50 stocks (depends on network)
- **Data Retention**: Results are kept in JSON and CSV for historical tracking
- **Resource Usage**: Low CPU and memory footprint, suitable for scheduled tasks

## Advanced Customization

To modify filter criteria, edit these lines in `run_scanner_simplified.py`:

```python
# Default filter settings
rsi_min, rsi_max = 30, 75      # Change RSI range
adx_min = 20                     # Change ADX threshold
min_volume_ratio = 1.2           # Change volume requirement
```

Or to change the stock list:

```python
def get_nse_stocks():
    """Get list of NSE F&O stocks to scan"""
    stocks = [
        # Add/remove stocks here
        'RELIANCE', 'TCS', 'HDFCBANK', ...
    ]
```

## Security Notes

- Never commit your `TELEGRAM_BOT_TOKEN` to version control
- Keep your Chat ID private
- The scanner doesn't send financial advice, only technical analysis results
- Always use stop losses and position sizing

## Support & Issues

If you encounter issues:

1. Check the logs: `tail -f /tmp/pcs_scanner.log`
2. Run manually to see error messages: `python run_scanner_simplified.py`
3. Verify network connectivity: `ping yahoo.com`
4. Check Telegram bot is active: Send `/start` to your bot

## Next Steps

1. Create your Telegram bot and get credentials
2. Set environment variables
3. Run manually first: `python run_scanner_simplified.py`
4. Once working, set up cron or scheduler
5. Monitor results in Telegram daily

Happy trading! 📈
