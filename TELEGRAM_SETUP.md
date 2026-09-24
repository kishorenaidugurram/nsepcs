# NSE PCS Scanner - Telegram Integration Setup

## 📱 Telegram Bot Configuration

### Step 1: Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send the command `/start`
3. Send the command `/newbot`
4. Follow the prompts:
   - Choose a name for your bot (e.g., "NSE Scanner Bot")
   - Choose a username (must end with "bot", e.g., "nsepcs_scanner_bot")
5. BotFather will provide you with a **TOKEN** (looks like: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### Step 2: Get Your Chat ID

1. Open Telegram and search for **@userinfobot**
2. Send any message (e.g., "hi")
3. The bot will reply with your User ID (a number like: `123456789`)

### Step 3: Configure Environment Variables

Set these environment variables before running the scanner:

```bash
# On Linux/Mac:
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"

# Example:
export TELEGRAM_BOT_TOKEN="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
export TELEGRAM_CHAT_ID="123456789"
```

### Step 4: Make it Permanent (Optional)

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
echo 'export TELEGRAM_BOT_TOKEN="your_token"' >> ~/.bashrc
echo 'export TELEGRAM_CHAT_ID="your_chat_id"' >> ~/.bashrc
source ~/.bashrc
```

Or create a `.env` file in the project directory and load it:

```bash
# .env file content:
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# To load: source .env
```

## 🚀 Running the Scanner

### With Telegram Configured

```bash
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"
python3 minimal_scanner_telegram.py
```

### Verify Telegram Connection

```bash
curl -X POST https://api.telegram.org/bot<YOUR_TOKEN>/sendMessage \
  -d chat_id=<YOUR_CHAT_ID> \
  -d text="Test message from NSE Scanner"
```

## 📊 Scanner Configuration

The scanner uses these default settings:

- **Min PCS Score**: 55
- **Min Liquidity Tier**: 3
- **Max Stocks to Scan**: 30
- **Min Volume Ratio**: 1.0x average
- **Pattern Detection**: All 5 main patterns enabled
  - RSI Oversold Bounce
  - Volume Breakout
  - Bollinger Band touches
  - MACD Crossovers
  - Above-average volume

## 🔧 Customization

Edit `minimal_scanner_telegram.py` to modify:

1. **Stock Universe** - Change `COMPLETE_NSE_FO_UNIVERSE` list
2. **Pattern Detection** - Modify the `detect_patterns()` function
3. **Telegram Format** - Edit `format_telegram_report()` function

## ⚠️ Troubleshooting

### "Connection tunnel failed" Error
- This indicates proxy/network issues blocking yfinance
- May need to run from a different network or configure proxy settings

### "Telegram Bot Token Invalid"
- Verify the token is copied correctly from BotFather
- Make sure there are no extra spaces

### "Telegram Chat ID Invalid"
- Ensure the chat ID is numeric (from userinfobot)
- Verify the bot has been started by the user

## 📝 Scheduled Execution

To run the scanner on a schedule (e.g., daily at market close):

```bash
# Using cron (edit with: crontab -e)
# Run daily at 3:30 PM IST (when market closes):
30 15 * * * export TELEGRAM_BOT_TOKEN="token"; export TELEGRAM_CHAT_ID="id"; cd /home/user/nsepcs && python3 minimal_scanner_telegram.py >> /var/log/nse_scanner.log 2>&1
```

## 📧 Email Alternative

If you prefer email instead of Telegram, modify the `send_telegram_message()` function to use SMTP:

```python
import smtplib
from email.mime.text import MIMEText

def send_email_report(message, recipient_email):
    msg = MIMEText(message)
    msg['Subject'] = 'NSE Scanner Daily Report'
    msg['From'] = 'your_email@gmail.com'
    msg['To'] = recipient_email
    
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login('your_email@gmail.com', 'your_app_password')
        server.sendmail(msg['From'], [recipient_email], msg.as_string())
```

## 🛠️ Support

For issues with:
- **Telegram Bot Creation**: See https://core.telegram.org/bots/tutorial
- **Market Data**: Visit https://finance.yahoo.com/
- **Python Script**: Check the error logs in the output file
