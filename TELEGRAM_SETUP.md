# Telegram Integration Setup Guide

This guide explains how to set up Telegram integration for the stock scanner to send results automatically to your Telegram chat.

## What You'll Need

1. **Telegram Bot Token** - From BotFather
2. **Telegram Chat ID** - Your personal chat or group chat ID

## Step-by-Step Setup

### 1. Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send the command `/start`
3. Send `/newbot`
4. Follow the prompts to name your bot
5. BotFather will give you a **Bot Token** that looks like:
   ```
   123456789:ABCDEFGhijklmnoPQRStuvwxyz1234567890
   ```
6. Copy and save this token

### 2. Get Your Telegram Chat ID

**Option A: Using a Bot (Recommended)**
1. Search for **@userinfobot** in Telegram
2. Send `/start`
3. The bot will reply with your Chat ID (a number)

**Option B: Manual Method**
1. Go to: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
2. Replace `<YOUR_BOT_TOKEN>` with your actual bot token
3. Send any message to your bot
4. Refresh the page - you'll see your chat ID in the response

### 3. Configure Telegram Credentials

Choose one of these methods:

#### Method A: Environment Variables (Recommended for Production)

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

Add these to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.) to make them permanent.

#### Method B: Configuration File

Create `~/.telegram_config.json`:

```json
{
  "bot_token": "your_bot_token_here",
  "chat_id": "your_chat_id_here"
}
```

Make sure to secure this file:
```bash
chmod 600 ~/.telegram_config.json
```

## Running the Scanner

### Simple Scanner (Recommended)
```bash
cd /home/user/nsepcs
python3 run_scanner_simple.py
```

This scanner:
- ✅ Detects current day breakouts with volume confirmation
- ✅ Calculates technical indicators (RSI, ADX, Volume)
- ✅ Sends results to Telegram automatically
- ✅ No complex dependencies required

### Advanced Scanner
```bash
cd /home/user/nsepcs
python3 run_scanner_and_send_telegram.py
```

This scanner includes:
- ✅ Advanced pattern detection (Cup & Handle, Double Bottom, etc.)
- ✅ Weekly validation on daily patterns
- ✅ Multiple technical indicators
- ✅ Enhanced filtering options

## Scheduling the Scanner (Cron Job)

To run the scanner automatically every day after market close:

1. Edit your crontab:
```bash
crontab -e
```

2. Add this line (runs at 3:45 PM IST, 30 min after market close):
```bash
45 15 * * 1-5 cd /home/user/nsepcs && /usr/bin/python3 run_scanner_simple.py >> /var/log/stock_scanner.log 2>&1
```

3. For the advanced scanner:
```bash
45 15 * * 1-5 cd /home/user/nsepcs && /usr/bin/python3 run_scanner_and_send_telegram.py >> /var/log/stock_scanner.log 2>&1
```

**Note:** Replace `15 45` with your desired time. Format is `HH MM`.

## Troubleshooting

### Bot not sending messages?

1. Make sure you've started a chat with your bot first
2. Verify the token and chat ID are correct
3. Check that the environment variables or config file are properly set
4. Run manually to see error messages:
   ```bash
   python3 run_scanner_simple.py
   ```

### "Telegram credentials not configured" message?

1. Verify environment variables:
   ```bash
   echo $TELEGRAM_BOT_TOKEN
   echo $TELEGRAM_CHAT_ID
   ```
2. If using config file, verify it exists:
   ```bash
   cat ~/.telegram_config.json
   ```

### No stocks found in results?

This can happen if:
- No stocks meet all filter criteria on that day
- Market conditions are bearish (low volume, no breakouts)
- Technical filters are too strict

Results are still sent to Telegram showing the scan was run.

## Testing Your Setup

1. **Test Telegram connection:**
   ```bash
   curl -X POST https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage \
     -d "chat_id=$TELEGRAM_CHAT_ID" \
     -d "text=Test message from stock scanner"
   ```

2. **Run a test scan:**
   ```bash
   python3 run_scanner_simple.py
   ```

You should receive the results on Telegram!

## Filter Criteria

### Simple Scanner Filters
- **RSI**: 30-75 (avoiding overbought/oversold)
- **ADX**: >= 20 (trending market confirmation)
- **Volume**: >= 1.2x average (above-average volume)
- **Price**: Above 20-day moving average
- **Breakout**: Above recent 20-day resistance with volume surge

### Advanced Scanner Filters (Customizable)
- **Chart Patterns**: Cup & Handle, Flat Base, Double Bottom, etc.
- **Timeframe**: Daily + Weekly Combined (Recommended)
- **Pattern Strength**: 70% minimum
- **Weekly Validation**: Confirms daily patterns on weekly timeframe

## Output

Results include:
- **Stock Symbol**: NSE ticker (e.g., RELIANCE, TCS)
- **Price**: Current closing price in INR
- **Strength Score**: 0-100% confidence level
- **Technical Indicators**: RSI, ADX, Volume ratio
- **Daily Change**: Percentage change from previous close

## Privacy & Security

- Your Bot Token grants access to your bot - **keep it secret!**
- Chat ID identifies your chat - handle with care
- Store credentials only in environment variables or secure config files
- Never commit tokens to version control

## Support

For issues or questions:
1. Check that Telegram app is updated
2. Verify bot token format (should contain a colon `:`)
3. Ensure you've started a conversation with the bot
4. Review logs if using cron: `tail -f /var/log/stock_scanner.log`

---

**Remember:** This scanner is for educational purposes. Always do your own research before trading!
