# Telegram Setup for NSE F&O PCS Scanner

## Required Configuration

To send stock scanner results to Telegram, you need to configure two environment variables:

### 1. Get Your Telegram Bot Token

1. Open Telegram and search for `@BotFather`
2. Start a chat and type `/start`
3. Type `/newbot` and follow the instructions
4. Save the HTTP API token provided (looks like: `123456789:ABCdefGHIjklmnoPQRstuvWXYZabcdefg`)

### 2. Get Your Chat ID

1. Create a Telegram bot or use `@userinfobot`
2. Send `/start` to the bot
3. The bot will reply with your User ID (this is your Chat ID)
4. Or forward a message from the bot to `@userinfobot` to get your Chat ID

### 3. Set Environment Variables

Set these environment variables before running the scanner:

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

Or add them to your `.bashrc` or `.bash_profile`:

```bash
echo 'export TELEGRAM_BOT_TOKEN="your_bot_token_here"' >> ~/.bashrc
echo 'export TELEGRAM_CHAT_ID="your_chat_id_here"' >> ~/.bashrc
source ~/.bashrc
```

### 4. Test the Configuration

Run the scanner:

```bash
python3 /home/user/nsepcs/run_scanner_telegram.py
```

Results will be sent to your Telegram account if properly configured.

## Current Status

**Telegram Configuration**: ❌ Not configured
- `TELEGRAM_BOT_TOKEN`: Not set
- `TELEGRAM_CHAT_ID`: Not set

To enable Telegram notifications, set the environment variables above.

## Example Output

Once configured, you'll receive messages like:

```
📈 NSE F&O PCS Scanner Results - 2024-10-19 14:30:00

✅ Found 5 stocks meeting filter criteria

🔥 HIGH CONFIDENCE (3):
• HDFCBANK - ₹1234.56 | RSI: 65.3 | Vol: 2.5x
• INFY - ₹2345.67 | RSI: 62.1 | Vol: 1.8x
• TCS - ₹3456.78 | RSI: 58.9 | Vol: 2.1x

🟡 MEDIUM CONFIDENCE (2):
• SBIN - ₹567.89 | RSI: 55.2 | Vol: 1.6x
• ITC - ₹678.90 | RSI: 52.4 | Vol: 1.5x
```
