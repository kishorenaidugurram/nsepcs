# NSE F&O PCS Scanner - Telegram Integration Setup

## Overview
This guide explains how to set up automated Telegram notifications for the PCS stock scanner to receive stock alerts directly on your phone.

## What You'll Need

1. **Telegram Bot Token** - A unique identifier for your bot
2. **Telegram Chat ID** - Your personal chat ID to receive messages
3. **Environment Variables** - Configuration to enable notifications

## Step-by-Step Setup

### Step 1: Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send the command `/start`
3. Send `/newbot`
4. Follow the prompts:
   - Name your bot (e.g., "NSE PCS Scanner")
   - Username must end with "bot" (e.g., "nse_pcs_scanner_bot")
5. Copy the **API Token** (looks like: `123456789:ABCdefGHIjklmnoPQRstuvwxyzABCDEfg`)
6. Save this token securely

### Step 2: Get Your Telegram Chat ID

1. Message your bot with `/start`
2. In your terminal, run:
   ```bash
   curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
   Replace `<YOUR_BOT_TOKEN>` with the token from Step 1

3. Look for the `"id"` field in the response - this is your **Chat ID**
   
   Example response:
   ```json
   {
     "ok": true,
     "result": [
       {
         "update_id": 123456789,
         "message": {
           "message_id": 1,
           "from": {
             "id": 987654321,  // <-- This is your Chat ID
             "is_bot": false,
             ...
           }
         }
       }
     ]
   }
   ```

### Step 3: Configure Environment Variables

Export the credentials in your shell or add to your system's environment:

```bash
# Method 1: Temporary (current terminal session only)
export TELEGRAM_BOT_TOKEN='your_bot_token_here'
export TELEGRAM_CHAT_ID='your_chat_id_here'

# Method 2: Permanent (add to ~/.bashrc or ~/.bash_profile)
echo "export TELEGRAM_BOT_TOKEN='your_bot_token_here'" >> ~/.bashrc
echo "export TELEGRAM_CHAT_ID='your_chat_id_here'" >> ~/.bashrc
source ~/.bashrc

# Method 3: Create a .env file in the project directory
cat > /home/user/nsepcs/.env << 'EOF'
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
EOF

# Load the .env file before running (add to your cron job or script)
set -a
source /home/user/nsepcs/.env
set +a
```

### Step 4: Verify Setup

Test your configuration:

```bash
export TELEGRAM_BOT_TOKEN='your_token'
export TELEGRAM_CHAT_ID='your_id'

python3 << 'EOF'
import os
import requests

token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')

if token and chat_id:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": "✅ NSE PCS Scanner - Telegram connection successful!"
    }
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print("Message sent successfully!" if response.status_code == 200 else f"Error: {response.text}")
else:
    print("❌ Credentials not set")
EOF
```

### Step 5: Set Up Automated Scanning (Cron Job)

Add a cron job to run the scanner at specific times:

```bash
# Edit crontab
crontab -e

# Add this line to run scanner at 9:30 AM every weekday
30 9 * * 1-5 cd /home/user/nsepcs && source .env && python3 run_pcs_scan.py >> /tmp/pcs_scan.log 2>&1

# Or run after market close at 3:45 PM
45 15 * * 1-5 cd /home/user/nsepcs && source .env && python3 run_pcs_scan.py >> /tmp/pcs_scan.log 2>&1
```

## Telegram Message Format

When configured, you'll receive messages like:

```
🎯 NSE F&O PCS SCAN RESULTS
2024-09-18 15:45 IST

🟢 HIGH Confidence (5):
  • RELIANCE: 82.3%
  • TCS: 78.9%
  • HDFCBANK: 76.1%
  ... +2 more

🟡 MEDIUM Confidence (8):
  • INFY: 68.5%
  ... +7 more

Total: 13 stocks
```

## Troubleshooting

### Issue: "Bot API token is invalid"
- ✅ Check that you copied the entire token correctly
- ✅ Verify token includes the colon (e.g., `123:ABC`)

### Issue: "Chat not found"
- ✅ Verify you got the correct Chat ID
- ✅ Make sure you've messaged the bot first with `/start`
- ✅ Check Chat ID is numeric (no letters)

### Issue: "Environment variables not found"
- ✅ Use `echo $TELEGRAM_BOT_TOKEN` to verify it's set
- ✅ If using `.env` file, make sure to `source .env` before running
- ✅ In cron jobs, source the `.env` file explicitly (shown above)

### Issue: Scanner runs but no message sent
- ✅ Run a test message to verify token works
- ✅ Check internet connection
- ✅ Verify bot is still active (sometimes bots are disabled if inactive)

## Security Notes

⚠️ **Important**: 
- Never commit your bot token or chat ID to version control
- Treat your token like a password
- If token is exposed, regenerate it via @BotFather
- Use `.env` file with `.gitignore` entry for credentials

```bash
# Add to .gitignore
echo ".env" >> /home/user/nsepcs/.gitignore
git add .gitignore
git commit -m "Add .env to gitignore"
```

## Next Steps

1. Complete the setup above
2. Run a test scan: `python3 run_pcs_scan.py`
3. Verify you receive a Telegram message
4. Set up the cron job for automated scanning
5. Enjoy receiving PCS stock alerts! 📱

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify credentials using the test script
3. Check scanner logs: `tail -f /tmp/pcs_scan.log`

---

**Last Updated**: 2026-09-18
**Compatible with**: Python 3.8+
