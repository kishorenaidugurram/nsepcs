# Quick Start: Telegram Scanner Setup

## TL;DR - Setup in 5 Minutes

### 1. Create Telegram Bot (1 minute)
```
1. Open Telegram → Search: @BotFather
2. Send: /newbot
3. Follow prompts, save the TOKEN you receive
```

### 2. Get Your Chat ID (1 minute)
```
1. Open Telegram → Search: @userinfobot  
2. Send: /start → Note your User ID
3. This is your CHAT_ID
```

### 3. Test Telegram Integration (1 minute)
```bash
export TELEGRAM_BOT_TOKEN="your_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"

python3.11 /home/user/nsepcs/telegram_scanner.py test
```
✅ You should receive a test message in Telegram

### 4. Run Demo Scan (1 minute)
```bash
TELEGRAM_BOT_TOKEN="your_token" TELEGRAM_CHAT_ID="your_id" \
  python3.11 /home/user/nsepcs/run_scan_demo.py
```
✅ Scan results will be sent to your Telegram

### 5. Set Up Auto-Run (1 minute)

**For Cron (Daily 9:15 AM IST):**
```bash
crontab -e
# Add this line:
15 9 * * 1-5 bash -c 'export TELEGRAM_BOT_TOKEN="token"; export TELEGRAM_CHAT_ID="id"; python3.11 /home/user/nsepcs/run_scan_demo.py' >> /tmp/nse_scan.log 2>&1
```

**For Manual Runs:**
```bash
# Just run anytime:
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"
python3.11 /home/user/nsepcs/run_scan_demo.py
```

## What Gets Sent to Telegram?

Example message:
```
📊 NSE F&O PCS Scanner Results
2026-10-16 15:30:00 IST

✅ Found 10 stocks matching criteria:

1. AXISBANK - Support near SMA20 + RSI: 66 (85%)
2. SBIN - Support near SMA20 + RSI: 65 (85%)
3. MARUTI - Support near SMA20 + RSI: 67 (85%)
... and 7 more stocks
```

## Choosing the Right Scanner

### `run_scan_demo.py` ✅ Recommended for scheduled tasks
- ✅ Works offline (uses synthetic data)
- ✅ No network issues
- ✅ Fast execution (~5 seconds)
- ✅ Perfect for testing
- ⚠️ Uses demo data (not real market data)

### `run_scan.py` (Real data - experimental)
- ✅ Uses real Yahoo Finance data
- ⚠️ May fail without proper network
- ⚠️ Requires internet access
- ❌ May have timeouts in restricted networks

## Troubleshooting

### "Telegram not configured" error
```bash
# Check if variables are set:
echo "Token: $TELEGRAM_BOT_TOKEN"
echo "Chat ID: $TELEGRAM_CHAT_ID"

# If empty, set them:
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

### "Failed to send to Telegram" (but configured)
- Check bot token is correct (should contain a colon)
- Check chat ID is numeric
- Verify network access to api.telegram.org
- Check bot isn't rate-limited

### Want real market data?
- `run_scan.py` needs network access
- Make sure YFinance can reach yahoo.com
- May fail in restricted networks (use demo instead)

## Making It Permanent

To auto-run daily without manual setup:

**Option 1: Add to ~/.bashrc**
```bash
echo 'export TELEGRAM_BOT_TOKEN="your_token"' >> ~/.bashrc
echo 'export TELEGRAM_CHAT_ID="your_chat_id"' >> ~/.bashrc
source ~/.bashrc
```

**Option 2: Create wrapper script**
```bash
cat > /usr/local/bin/nse-scan.sh << 'EOF'
#!/bin/bash
export TELEGRAM_BOT_TOKEN="token"
export TELEGRAM_CHAT_ID="id"
python3.11 /home/user/nsepcs/run_scan_demo.py
EOF
chmod +x /usr/local/bin/nse-scan.sh
```

Then use in cron: `0 9 * * 1-5 /usr/local/bin/nse-scan.sh`

## More Help

- Full setup guide: `TELEGRAM_SETUP.md`
- Test connection: `python3.11 telegram_scanner.py test`
- Check status: `python3.11 telegram_scanner.py config`
- Send demo results: `python3.11 telegram_scanner.py demo`

## Security Reminder

🔐 Never commit credentials to git!
```bash
# Bad:
TELEGRAM_BOT_TOKEN="123..." git add file.py

# Good:
export TELEGRAM_BOT_TOKEN="123..."  # In terminal, not in code
python3.11 scanner.py
```

## Questions?

Check `TELEGRAM_SETUP.md` for detailed troubleshooting or create a GitHub issue.
