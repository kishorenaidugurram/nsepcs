# NSE F&O PCS Scanner - Telegram Integration

## Overview

The scheduled scanner automatically runs daily and sends stock screening results to your Telegram account.

## What It Does

The scanner:
1. 🔍 **Scans** 50+ NSE F&O stocks against technical criteria
2. 📊 **Analyzes** RSI, ADX, Volume, Moving Averages, and Chart Patterns
3. 📈 **Identifies** bullish breakout stocks and chart patterns
4. 📤 **Sends** qualifying stocks via Telegram with detailed metrics

## Filter Criteria

Default filters applied:
- **RSI Range:** 30-75 (momentum strength)
- **ADX Minimum:** 20 (trend strength)
- **Volume Ratio:** 1.2x average (confirmation)
- **Pattern Strength:** 65%+ (chart patterns)
- **Trend:** Price > Moving Averages (bullish alignment)

## Setup Instructions

### Step 1: Create Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/start` and follow instructions
3. Send `/newbot` to create a new bot
4. Follow the prompts and save your **BOT TOKEN**
5. Send `/token` to BotFather to retrieve your token anytime

### Step 2: Get Your Chat ID

1. Search for your new bot (use the @username from BotFather)
2. Send `/start` to your bot
3. Open this URL in browser (replace TOKEN): 
   ```
   https://api.telegram.org/botTOKEN/getUpdates
   ```
4. Look for `"chat":{"id":123456789}` - that's your **CHAT ID**

### Step 3: Configure Environment Variables

Add these to your environment:

```bash
export TELEGRAM_BOT_TOKEN='your_bot_token_here'
export TELEGRAM_CHAT_ID='your_chat_id_here'
```

Or create a `.env` file in the project:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

Then load it:
```bash
source .env
```

### Step 4: Run Scanner Manually

```bash
# Demo mode (sample data, no network required)
python3 /tmp/claude-0/-home-user-nsepcs/2d3fbbed-c92f-5a8b-9471-670eeb12fbf9/scratchpad/demo_scanner.py

# Live mode (requires network access to Yahoo Finance)
python3 /tmp/claude-0/-home-user-nsepcs/2d3fbbed-c92f-5a8b-9471-670eeb12fbf9/scratchpad/simple_scanner.py
```

## Message Format

You'll receive Telegram messages like:

```
📊 NSE F&O PCS Scanner Results
2026-10-21 09:18 IST
✅ Found 10 qualifying stocks
========================================

1. ASIANPAINT 📈 
   Price: ₹2845.60
   Strength: 89% | RSI: 73.5
   ADX: 33.8 | Vol Ratio: 2.65x

2. MARUTI 📈 
   Price: ₹12458.35
   Strength: 87% | RSI: 69.5
   ADX: 31.2 | Vol Ratio: 2.45x

... (and more stocks)
```

## Customization

### Modify Filter Criteria

Edit the scanner script and change these values:

```python
config = {
    'rsi_min': 30,           # Lower = more signals
    'rsi_max': 75,           # Higher = includes overbought
    'adx_min': 20,           # Lower = weaker trends included
    'pattern_strength_min': 65,  # Lower = more patterns
    'min_volume_ratio': 1.2,    # Lower = lower volume required
}
```

### Adjust Scan Time

The scanner runs on a schedule. To change timing:

1. Edit the cron job or scheduled task
2. Or modify the scheduler in your deployment platform

## Troubleshooting

### "Telegram credentials not configured"
- Ensure environment variables are set
- Check variable names (case-sensitive)
- Verify token and chat ID are correct

### No stocks found
- Lower `pattern_strength_min` from 65 to 50
- Reduce `min_volume_ratio` from 1.2 to 1.0
- Expand RSI range (e.g., 25-80)

### Network errors
- Check internet connection
- Verify proxy configuration
- Yahoo Finance may be temporarily unavailable

### Bot doesn't respond
- Verify bot token is correct
- Check chat ID is correct
- Ensure bot has message permissions

## File Locations

- **Demo Scanner:** `/tmp/.../scratchpad/demo_scanner.py`
- **Live Scanner:** `/tmp/.../scratchpad/simple_scanner.py`
- **Full Scanner:** `/tmp/.../scratchpad/scan_and_send.py`
- **Results CSV:** `/tmp/.../scratchpad/scanner_results_*.csv`

## Support

For issues with:
- **Telegram Setup:** Check official Telegram bot documentation
- **Stock Analysis:** Review technical indicators in the code
- **Network/Proxy:** See `/root/.ccr/README.md`

## Security Notes

⚠️ **Never share your:**
- Bot token
- Chat ID
- API keys or tokens

Keep environment variables secure and use `.env` files that are gitignored.

## Next Steps

1. ✅ Set up Telegram bot via BotFather
2. ✅ Configure environment variables
3. ✅ Test with demo scanner
4. ✅ Enable live scanner when ready
5. ✅ Set up scheduled runs for daily scans
