# NSE Stock Scanner - Telegram Integration Setup

This guide explains how to set up the automatic stock scanner with Telegram notifications.

## Prerequisites

- Python 3.8+
- Telegram account
- A Telegram bot token (from BotFather)
- Your Telegram chat ID

## Step 1: Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/start` and follow the prompts
3. Send `/newbot` to create a new bot
4. Follow the instructions:
   - Name your bot (e.g., "NSE Stock Scanner")
   - Choose a username ending in "bot" (e.g., "nse_stock_scanner_bot")
5. BotFather will provide you with a **Bot Token** - save this!

Example token: `123456789:ABCDEfghIjklMNOpqrSTUVwxyz`

## Step 2: Get Your Chat ID

1. Open the bot in Telegram
2. Send any message to your bot (e.g., `/start`)
3. Visit: `https://api.telegram.org/bot{YOUR_BOT_TOKEN}/getUpdates`
   - Replace `{YOUR_BOT_TOKEN}` with your actual token
4. Look for the `"chat"` section and find your **Chat ID** - save this!

Example chat ID: `123456789`

## Step 3: Configure the Scanner

1. Copy the example configuration:
```bash
cp telegram_config.example.json telegram_config.json
```

2. Edit `telegram_config.json`:
```json
{
  "telegram": {
    "bot_token": "YOUR_BOT_TOKEN_HERE",
    "chat_id": "YOUR_CHAT_ID_HERE"
  },
  "scanner": {
    "rsi_min": 30,
    "rsi_max": 70,
    "adx_min": 20,
    "ma_support": true,
    "ma_tolerance": 5,
    "ma_type": "EMA",
    "pattern_strength_min": 65,
    ...
  }
}
```

Replace placeholders with your actual credentials.

## Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 5: Run the Scanner

### Option A: One-time run
```bash
python telegram_scanner.py
```

### Option B: Schedule with Cron (Linux/Mac)

Add to your crontab (`crontab -e`):

```bash
# Run scanner every weekday at 4 PM (after market close in IST)
0 16 * * 1-5 cd /path/to/nsepcs && python telegram_scanner.py >> telegram_scanner.log 2>&1
```

### Option C: Schedule with Task Scheduler (Windows)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger to run daily at desired time
4. Set action to run `python telegram_scanner.py`

## Configuration Options

### Scanner Filters

- **rsi_min/rsi_max**: RSI range (default: 30-70)
- **adx_min**: Minimum ADX value for trend strength (default: 20)
- **ma_support**: Check if price is above moving average (default: true)
- **pattern_strength_min**: Minimum pattern strength percentage (default: 65)
- **lookback_days**: Number of days to lookback for patterns (default: 20)
- **volume_breakout_ratio**: Minimum volume ratio for breakout (default: 2.0x)

### Pattern Filters

Enable/disable specific chart patterns:
- `current_day_breakout`: Today's breakouts
- `cup_and_handle`: Cup and handle patterns
- `flat_base`: Flat base breakouts
- `bump_and_run`: Bump and run reversal
- `rectangle_bottom`: Rectangle bottom patterns
- `double_bottom`: Double bottom formations
- `three_rising_valleys`: Three rising valleys
- `rounding_bottom`: Rounding bottom patterns

### Stock Universe

Choose which stocks to scan:
- **"Nifty 50"**: Top 50 NSE stocks
- **"Bank Nifty"**: Banking sector stocks
- **"Pharma Stocks"**: Pharmaceutical stocks
- **"IT Stocks"**: IT sector stocks
- **"All F&O"**: All 208 F&O eligible stocks

## Telegram Message Format

The scanner sends two types of messages:

### 1. Summary Message
Shows total matching stocks and filter criteria used

### 2. Detailed Messages
For each matching stock, shows:
- Stock symbol and current price
- Detected patterns
- Pattern strength and confidence
- Success rate and PCS suitability

## Troubleshooting

### "Config file not found"
- Make sure you copied `telegram_config.example.json` to `telegram_config.json`
- Check the file is in the same directory as `telegram_scanner.py`

### "Invalid Telegram credentials"
- Verify your bot token and chat ID are correct
- Make sure your bot has access to send messages
- Try the bot manually first by sending it a message

### "No stocks matched"
- Adjust filter criteria to be less strict
- Lower `pattern_strength_min` value
- Expand RSI range
- Increase `lookback_days`

### "Failed to fetch stock data"
- Check internet connection
- Yahoo Finance might be temporarily unavailable
- Try running again later

## Example Use Cases

### For Conservative PCS Traders
```json
{
  "pattern_strength_min": 75,
  "rsi_min": 35,
  "rsi_max": 65,
  "adx_min": 25
}
```

### For Aggressive Traders
```json
{
  "pattern_strength_min": 55,
  "rsi_min": 20,
  "rsi_max": 80,
  "adx_min": 15
}
```

### For Nifty 50 Focus
```json
{
  "universe": "Nifty 50",
  "pattern_strength_min": 70
}
```

## Security Notes

⚠️ **IMPORTANT:**
- Never commit `telegram_config.json` to version control
- Keep your bot token and chat ID private
- Use `.gitignore` to exclude the config file:
  ```
  telegram_config.json
  ```

## Support

For issues or questions:
1. Check the logs in console output
2. Verify Telegram credentials are correct
3. Ensure you have internet connectivity
4. Make sure yfinance can reach Yahoo Finance

## Advanced: Custom Schedule

To run at specific times or with custom intervals, create a `run_scanner.sh`:

```bash
#!/bin/bash
cd /path/to/nsepcs
python telegram_scanner.py
```

Then schedule with cron or your preferred scheduler.
