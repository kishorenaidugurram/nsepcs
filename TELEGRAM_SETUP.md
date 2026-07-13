# Telegram Stock Scanner Setup Guide

## Overview
The `telegram_scanner.py` script scans NSE F&O stocks for trading patterns and sends qualifying stocks to Telegram.

## Prerequisites
- Telegram bot token (from BotFather)
- Telegram chat ID
- Environment variables configured

## Step 1: Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send the command `/newbot`
3. Follow the prompts to create your bot
4. BotFather will provide your **Bot Token** (save this!)

Example token format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

## Step 2: Get Your Chat ID

1. Open Telegram and search for **@userinfobot**
2. Send any message to this bot
3. It will reply with your **User ID** / Chat ID
4. Save this ID

## Step 3: Set Environment Variables

### Option A: Command Line (One-time)
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
python3 telegram_scanner.py
```

### Option B: Create .env file
Create a file named `.env` in the project root:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

Then load it before running:
```bash
set -a
source .env
set +a
python3 telegram_scanner.py
```

### Option C: Permanently (Add to ~/.bashrc or ~/.bash_profile)
```bash
echo 'export TELEGRAM_BOT_TOKEN="your_bot_token_here"' >> ~/.bashrc
echo 'export TELEGRAM_CHAT_ID="your_chat_id_here"' >> ~/.bashrc
source ~/.bashrc
```

## Running the Scanner

### Manual Run
```bash
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"
python3 telegram_scanner.py
```

### Scheduled Run (Cron Job)
To run the scanner daily at 9:30 AM:

```bash
# Edit crontab
crontab -e

# Add this line:
30 9 * * 1-5 cd /home/user/nsepcs && export TELEGRAM_BOT_TOKEN="your_token" && export TELEGRAM_CHAT_ID="your_chat_id" && python3 telegram_scanner.py >> /tmp/stock_scan.log 2>&1
```

## Filter Criteria

The scanner looks for stocks that meet ALL of these criteria:

1. **RSI**: 30-75 (momentum in sweet spot)
2. **ADX**: ≥ 20 (trend strength)
3. **Volume Ratio**: ≥ 1.2x (current day volume vs 20-day average)
4. **Current Day Breakout**: Price breaks 20-day high with volume confirmation
5. **Price above EMA20**: Trending higher

## Stocks Scanned

Default scans the first 40 NSE F&O stocks (largest, most liquid):
- Nifty, Bank Nifty, Reliance, TCS, HDFCBANK
- INFY, ICICIBANK, SBIN, LT, ITC
- And 30 more large-cap stocks

To modify the list, edit `COMPLETE_NSE_FO_UNIVERSE` in `telegram_scanner.py`

## Customizing Filters

Edit the `main()` function in `telegram_scanner.py`:

```python
results = scanner.scan_stocks(
    COMPLETE_NSE_FO_UNIVERSE[:40],  # Change 40 to scan more/fewer stocks
    rsi_min=30,        # Change RSI minimum
    rsi_max=75,        # Change RSI maximum
    adx_min=20,        # Change ADX minimum
    min_volume_ratio=1.2,  # Change volume ratio requirement
    enable_breakout=True   # Set to False to disable breakout detection
)
```

## Expected Output

When stocks are found, you'll receive a Telegram message like:

```
📈 Stocks Meeting Filter Criteria 📈

Found: 5 stocks
Time: 14:32 IST

1. RELIANCE
   Price: ₹2,850.45
   RSI: 52.3 | ADX: 25.8
   Volume: 2.15x | Breakout: 1.23%

2. HDFCBANK
   Price: ₹1,650.20
   RSI: 58.1 | ADX: 22.5
   Volume: 1.89x | Breakout: 0.87%

... and 3 more stocks
```

## Troubleshooting

### "No stocks found"
- Market might be closed
- Adjust filters to be less strict (lower RSI requirements, lower ADX minimum)
- Check if data is loading correctly

### "Error sending to Telegram"
- Verify bot token is correct
- Verify chat ID is correct
- Check internet connection
- Ensure bot has permission to message you

### Connection timeout
- Check internet connectivity
- Try running again (API might be temporary down)
- Check if Telegram API is accessible from your location

## Notes

- The script respects your time zone (Asia/Kolkata - IST)
- Results are sorted by volume ratio (highest first)
- Top 15 stocks are sent to Telegram (prevents message overflow)
- All other stocks are counted but not displayed individually
- Script handles errors gracefully and sends error messages to Telegram

## Advanced: PCS-Specific Filters

For Put Credit Spread trading, you might want to adjust filters:
- **Conservative**: RSI 40-65, ADX 25+, Volume 2x+
- **Moderate**: RSI 30-75, ADX 20+, Volume 1.5x+
- **Aggressive**: RSI 25-80, ADX 15+, Volume 1.2x+

## Support

For issues or questions:
1. Check that environment variables are set correctly
2. Run manually to see error messages
3. Check the log file for debugging
