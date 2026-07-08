# 📱 Telegram Integration Setup Guide

## Quick Start

Follow these steps to set up stock scanner results to be sent to your Telegram:

### Step 1: Create a Telegram Bot

1. **Open Telegram** and search for `@BotFather`
2. **Start a conversation** and send: `/start`
3. **Create a new bot** by sending: `/newbot`
4. **Follow the prompts** and name your bot (e.g., "NSE Stock Scanner")
5. **Copy the Bot Token** - you'll see it in the format: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`

### Step 2: Get Your Chat ID

1. **Create a private chat** with your bot or a group where you want results
2. **Send any message** to the bot (e.g., "test")
3. **Get your Chat ID** using this command:
   ```bash
   curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates"
   ```
4. **Look for the response** and find `"id"` under `"chat"` - that's your Chat ID

### Step 3: Configure Environment Variables

#### Option A: Set Temporarily (Current Session)
```bash
export TELEGRAM_BOT_TOKEN="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
export TELEGRAM_CHAT_ID="987654321"
```

#### Option B: Set Permanently (Add to ~/.bashrc or ~/.zshrc)
```bash
echo 'export TELEGRAM_BOT_TOKEN="your_token_here"' >> ~/.bashrc
echo 'export TELEGRAM_CHAT_ID="your_chat_id_here"' >> ~/.bashrc
source ~/.bashrc
```

#### Option C: Create .env File
Create a file named `.env` in the scanner directory:
```
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=987654321
```

Then load it before running:
```bash
source .env
```

### Step 4: Run the Scanner

#### Basic Usage
```bash
python3 simple_scanner.py --telegram
```

#### With Options
```bash
# Scan 100 stocks instead of 50
python3 simple_scanner.py --limit 100 --telegram

# Scan and save to file
python3 simple_scanner.py --telegram --file results.csv

# Run using shell script
bash RUN_SCANNER.sh 100 65
```

### Step 5: Verify Setup

Test your Telegram integration:
```bash
python3 -c "
from simple_scanner import SimpleScanner
scanner = SimpleScanner()
if scanner.send_telegram_message('✅ Scanner is ready!'):
    print('✅ Telegram integration working!')
else:
    print('❌ Check your bot token and chat ID')
"
```

## Command-Line Options

```
python3 simple_scanner.py [OPTIONS]

Options:
  --telegram              Send results to Telegram
  --limit N               Number of stocks to scan (default: 50)
  --file FILENAME         Save results to CSV file
  --help                  Show help message
```

## Telegram Bot Features

Your scanner will:
- 📊 Send scan start notification
- 🔍 Send progress updates every 20 stocks
- ✅ Send detailed results with top matches
- 📈 Include stock price, RSI, volume, and signals
- 📎 Optionally send Excel file with all results

## Example Telegram Message

```
📈 Stock Scanner Results
Generated: 2026-07-08 15:30 IST

🎯 Found: 15 stocks matching criteria

1. RELIANCE
   Price: ₹2,845.50
   RSI: 55.2 | Vol: 2.34x
   ✓ Healthy RSI (55.2)
   ✓ Above avg volume (2.34x)
   ✓ Above SMA20 (Uptrend)

... and 14 more stocks
```

## Troubleshooting

### Issue: "Telegram credentials not set"
**Solution**: Make sure environment variables are exported:
```bash
echo $TELEGRAM_BOT_TOKEN
echo $TELEGRAM_CHAT_ID
```

### Issue: "Failed to send to Telegram"
**Solution**: Verify your bot token and chat ID are correct:
```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getMe"
```

### Issue: "No stocks found"
**Solution**: Try lowering the minimum score filter or adjust indicators

## Scheduling Automated Scans

### Linux/Mac (using crontab)
```bash
# Edit crontab
crontab -e

# Add this line to scan daily at 3:30 PM IST (after market close)
30 9 * * 1-5 cd /home/user/nsepcs && export TELEGRAM_BOT_TOKEN="your_token" && export TELEGRAM_CHAT_ID="your_chat_id" && python3 simple_scanner.py --limit 100 --telegram
```

### Windows (using Task Scheduler)
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily at 3:30 PM
4. Set action: Run `python3 simple_scanner.py --limit 100 --telegram`
5. Set working directory to scanner folder

## Filter Criteria

The scanner uses these default filters:
- **RSI**: 30-75 (healthy range)
- **Volume**: >1.0x average
- **Trend**: Above 20-day EMA/SMA
- **Minimum Score**: 40/100

Adjust these in the code if needed.

## Support

For issues with:
- **Telegram**: Check @BotFather or Telegram API docs
- **Stock Data**: Ensure yfinance can reach Yahoo Finance
- **Scanner**: Review simple_scanner.py for custom indicators

---

**Happy Trading! 📈**
