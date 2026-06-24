# Telegram Bot Setup Guide

To send stock scanner results to Telegram, follow these steps:

## 1. Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Start the chat and send `/start`
3. Send `/newbot`
4. Choose a name for your bot (e.g., "Stock Scanner Bot")
5. BotFather will provide you with a **BOT TOKEN** (looks like: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)
6. Save this token safely

## 2. Get Your Chat ID

**Option A: Using the bot**
1. Start a chat with your new bot
2. Send any message
3. Go to: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Replace `<YOUR_BOT_TOKEN>` with your actual bot token
5. Look for `"chat":{"id":123456789}` - that's your **CHAT ID**

**Option B: Using another bot**
1. Search for **@userinfobot** on Telegram
2. Start the chat and it will show your User ID (Chat ID)

## 3. Set Environment Variables

Set these environment variables in your system:

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

### On Linux/Mac (Add to ~/.bashrc or ~/.zshrc):
```bash
echo 'export TELEGRAM_BOT_TOKEN="your_token"' >> ~/.bashrc
echo 'export TELEGRAM_CHAT_ID="your_chat_id"' >> ~/.bashrc
source ~/.bashrc
```

### On Windows (Command Prompt):
```cmd
setx TELEGRAM_BOT_TOKEN "your_token"
setx TELEGRAM_CHAT_ID "your_chat_id"
```

## 4. Verify Setup

Run the test script:
```bash
python3 /home/user/nsepcs/test_telegram.py
```

## 5. Run the Scanner

Once configured, run:
```bash
python3 /home/user/nsepcs/telegram_scanner.py
```

## For Scheduled/Routine Execution

If running as a scheduled task, ensure the environment variables are set in your shell profile or in the cron job:

```bash
0 9 * * 1-5 /bin/bash -c 'export TELEGRAM_BOT_TOKEN="..."; export TELEGRAM_CHAT_ID="..."; python3 /home/user/nsepcs/telegram_scanner.py' >> /tmp/stock_scanner.log 2>&1
```

---

**Need Help?**
- Telegram Bot API Docs: https://core.telegram.org/bots
- BotFather Help: https://telegram.me/botfather
