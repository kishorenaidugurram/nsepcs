# NSE F&O PCS Scanner - Telegram Setup Guide

## Overview
This guide explains how to set up and run the NSE F&O PCS Scanner with Telegram integration for automated daily scans.

## Prerequisites

### 1. Create a Telegram Bot
1. Open Telegram and search for **@BotFather**
2. Send `/start` to begin
3. Send `/newbot` to create a new bot
4. Follow the prompts to name your bot
5. Copy the **Bot Token** (looks like: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### 2. Get Your Chat ID
1. Search for **@userinfobot** on Telegram
2. Send any message to it
3. It will reply with your User ID (your **Chat ID**)

### 3. Set Environment Variables
Create or update your environment with these variables:

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

For persistent setup (if using cron):
Add to your `.bashrc` or `.bash_profile`:
```bash
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_id"
```

## Running the Scanner

### Option 1: Simple Scanner (Recommended)
```bash
cd /home/user/nsepcs
python3 simple_scanner.py --limit 50
```

### Option 2: All Stocks
```bash
python3 simple_scanner.py --all
```

### Option 3: Custom Limit
```bash
python3 simple_scanner.py --limit 30
```

## Setting Up Automated Daily Scans

### Using Cron (Linux/Mac)

1. Edit your crontab:
```bash
crontab -e
```

2. Add one of these lines for daily scans at specific times:

**9:15 AM every trading day (market opening):**
```bash
15 9 * * 1-5 cd /home/user/nsepcs && TELEGRAM_BOT_TOKEN="your_token" TELEGRAM_CHAT_ID="your_id" python3 simple_scanner.py --limit 50
```

**3:45 PM every trading day (market closing):**
```bash
45 15 * * 1-5 cd /home/user/nsepcs && TELEGRAM_BOT_TOKEN="your_token" TELEGRAM_CHAT_ID="your_id" python3 simple_scanner.py --limit 50
```

**Every 2 hours during market hours:**
```bash
30 */2 * * 1-5 cd /home/user/nsepcs && TELEGRAM_BOT_TOKEN="your_token" TELEGRAM_CHAT_ID="your_id" python3 simple_scanner.py --limit 30
```

3. Save and exit (Ctrl+X in nano, `:wq` in vim)

### Using GitHub Actions (Cloud-based)

Create `.github/workflows/daily-scan.yml`:

```yaml
name: NSE F&O Daily Scan

on:
  schedule:
    - cron: '15 4 * * 1-5'  # 9:45 AM IST (UTC 4:15 AM)
  workflow_dispatch:

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install pandas numpy yfinance requests
      
      - name: Run scanner
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: python3 simple_scanner.py --limit 50
```

Then add secrets in GitHub:
- Go to Settings > Secrets and variables > Actions
- Add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`

## Scanner Output

The scanner will:

1. **Scan through selected stocks** (limit: 30-50 by default)
2. **Check filter criteria:**
   - RSI between 30-75
   - ADX >= 20
   - Volume >= 1.2x average
   
3. **Detect patterns:**
   - Current day breakouts
   - Volume confirmation

4. **Send to Telegram:**
   - List of qualifying stocks
   - Strength score (0-100%)
   - Current price and RSI
   
5. **Save results:**
   - CSV file with results
   - File named: `scan_results_YYYYMMDD_HHMMSS.csv`

## Example Output

```
🎯 NSE F&O PCS Scan Results
📅 2024-10-05 15:45 IST

📊 Found 15 stocks

1. RELIANCE @ ₹2850.45 (Strength: 89%, RSI: 62.3)
2. HDFCBANK @ ₹1920.30 (Strength: 85%, RSI: 58.1)
3. INFY @ ₹1450.75 (Strength: 78%, RSI: 55.4)
...

📈 Avg Strength: 82.1%
```

## Troubleshooting

### "No stocks found"
- The network connection might not support yfinance
- Try increasing the limit: `--all`
- Wait a few minutes and retry (data sync delay)

### "Telegram credentials not set"
- Verify environment variables are exported:
  ```bash
  echo $TELEGRAM_BOT_TOKEN
  echo $TELEGRAM_CHAT_ID
  ```
- Both should show your actual values, not blank

### "Connection error from yfinance"
- May require VPN or proxy configuration
- Check network connectivity:
  ```bash
  curl -I https://finance.yahoo.com
  ```

### CSV file not saving
- Check write permissions in directory:
  ```bash
  ls -la /home/user/nsepcs/
  ```
- Make sure the script runs with proper permissions

## Customizing the Scanner

Edit `simple_scanner.py` to change filter criteria:

```python
# In the SimplePCSScanner.check_basic_criteria() method:
rsi_ok = 25 <= current_rsi <= 80      # Change RSI range
adx_ok = current_adx >= 15             # Change ADX minimum
volume_ok = current_volume >= (avg_volume * 1.0)  # Change volume ratio
```

## Support

For issues with:
- **Telegram setup**: See Telegram Bot API docs
- **Cron scheduling**: Check `man crontab`
- **Scanner logic**: Edit the `SimplePCSScanner` class in `simple_scanner.py`

---

**Happy Trading!** 📈
