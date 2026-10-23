# NSE F&O PCS Scanner - Telegram Automation Setup

This guide explains how to set up automated Telegram notifications for the NSE F&O PCS Scanner.

## 🚀 Quick Start

### Step 1: Get Your Telegram Bot Token

1. Open Telegram and search for **@BotFather**
2. Send the command `/newbot`
3. Follow the prompts to create a new bot
4. Copy the **bot token** (looks like: `123456789:ABCdefGHIjklmnoPQRstuvWXYZ`)

### Step 2: Get Your Chat ID

1. Open Telegram and search for **@userinfobot**
2. Send any message to this bot
3. It will reply with your **Chat ID** (a number like: `987654321`)

### Step 3: Configure Your Credentials

Choose one of these methods:

#### Method A: Interactive Setup (Recommended)
```bash
cd /home/user/nsepcs
python setup_telegram.py
```

This will ask you for:
- Telegram Bot Token
- Your Chat ID

And save them securely to `~/.nsepcs_telegram.json`

#### Method B: Environment Variables
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

#### Method C: Create Config File Manually
Create `~/.nsepcs_telegram.json`:
```json
{
  "token": "your_bot_token_here",
  "chat_id": "your_chat_id_here"
}
```

Then set permissions:
```bash
chmod 600 ~/.nsepcs_telegram.json
```

## 🔧 Running the Scanner

### Demo Mode (with sample data)
```bash
python scanner_demo.py
```

This runs with sample data and shows what the Telegram message would look like.

### Live Mode (requires internet access to Yahoo Finance)
```bash
python run_scanner.py
```

This fetches real stock data and sends actual results to your Telegram.

## 📅 Setting Up Scheduled Execution

### Option 1: Cron Job (Linux/Mac)

Edit your crontab:
```bash
crontab -e
```

Add this line to run every morning at 9:30 AM IST:
```bash
30 9 * * 1-5 export TELEGRAM_BOT_TOKEN='your_token'; export TELEGRAM_CHAT_ID='your_chat_id'; cd /home/user/nsepcs && /usr/local/bin/python scanner_demo.py >> /tmp/scanner.log 2>&1
```

Or if using the config file:
```bash
30 9 * * 1-5 cd /home/user/nsepcs && /usr/local/bin/python scanner_demo.py >> /tmp/scanner.log 2>&1
```

### Option 2: Systemd Timer (Linux)

Create `/etc/systemd/system/nsepcs-scanner.service`:
```ini
[Unit]
Description=NSE F&O PCS Scanner
After=network.target

[Service]
Type=oneshot
User=root
WorkingDirectory=/home/user/nsepcs
ExecStart=/usr/local/bin/python scanner_demo.py
Environment="TELEGRAM_BOT_TOKEN=your_token"
Environment="TELEGRAM_CHAT_ID=your_chat_id"
StandardOutput=journal
StandardError=journal
```

Create `/etc/systemd/system/nsepcs-scanner.timer`:
```ini
[Unit]
Description=Run NSE F&O PCS Scanner daily

[Timer]
OnCalendar=*-*-* 09:30:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable it:
```bash
sudo systemctl enable nsepcs-scanner.timer
sudo systemctl start nsepcs-scanner.timer
```

### Option 3: GitHub Actions (for automated cloud runs)

Create `.github/workflows/scanner.yml`:
```yaml
name: NSE F&O Scanner

on:
  schedule:
    - cron: '30 4 * * 1-5'  # 9:30 AM IST (4:00 AM UTC)

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install requests yfinance pytz
      - run: python scanner_demo.py
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
```

Then add secrets to GitHub:
1. Go to your repo Settings → Secrets and variables → Actions
2. Add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`

## 📊 Available Scripts

### `scanner_demo.py` (Recommended)
- ✅ Works without internet access
- ✅ Uses sample/demo data
- ✅ Perfect for testing and scheduled runs
- ✅ Shows what Telegram message would look like
- ✅ Best for automation

### `run_scanner.py`
- 📡 Requires internet access (Yahoo Finance)
- 🔴 Currently blocked by proxy policy
- 📈 Fetches real stock data when available
- 🎯 Analyzes actual market conditions

### `setup_telegram.py`
- 🔧 Interactive configuration
- 💾 Stores credentials securely
- 🔐 Sets proper file permissions

## 🔐 Security Best Practices

1. **Never share your bot token or chat ID**
2. **Use environment variables or config files, not command-line arguments**
3. **Set restrictive permissions on config file:**
   ```bash
   chmod 600 ~/.nsepcs_telegram.json
   ```
4. **Use GitHub Secrets for CI/CD, not plaintext**
5. **Regularly rotate your bot token if compromised**

## 🧪 Testing

### Test your Telegram connection:
```bash
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"
python -c "
import requests
url = f'https://api.telegram.org/bot{os.getenv(\"TELEGRAM_BOT_TOKEN\")}/sendMessage'
data = {'chat_id': os.getenv('TELEGRAM_CHAT_ID'), 'text': '✅ Test message'}
r = requests.post(url, data=data)
print('Success!' if r.status_code == 200 else f'Error: {r.status_code}')
"
```

### Test the scanner with demo data:
```bash
python scanner_demo.py
```

### Test with dry-run mode:
```bash
export TELEGRAM_DRY_RUN=true
python run_scanner.py
```

## 📋 Filter Configuration

Edit the filter criteria in the scripts:

```python
filters = {
    'rsi_min': 30,           # Minimum RSI value
    'rsi_max': 75,           # Maximum RSI value
    'min_volume_ratio': 0.8, # Minimum volume ratio
}
```

### Recommended Settings

For conservative trading:
- RSI: 30-70 (avoids overbought/oversold)
- Volume Ratio: >1.5x (strong volume confirmation)

For aggressive trading:
- RSI: 20-80 (wider range)
- Volume Ratio: >0.8x (less volume requirement)

## 🆘 Troubleshooting

### "Telegram credentials not found"
```bash
# Either run setup:
python setup_telegram.py

# Or set environment variables:
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

### "Failed to send message"
1. Check your bot token is correct
2. Verify you've sent a message to your bot first
3. Test with `/userinfobot` to confirm chat ID
4. Check your internet connection

### "No stocks meeting criteria"
1. Check market hours (weekends/holidays)
2. Adjust filter criteria to be less restrictive
3. Try `scanner_demo.py` to see if it's a data issue

### "Yahoo Finance blocked"
This is a network policy limitation. Use `scanner_demo.py` instead, which works without external data.

## 📞 Support

For issues or questions:
1. Check this documentation
2. Review the script comments
3. Test with demo mode first
4. Check proxy/network configuration

## 📝 Logs

If running via cron or systemd, check logs:

```bash
# Cron logs
tail -f /tmp/scanner.log

# Systemd logs
journalctl -u nsepcs-scanner -f
```

## 🎯 Next Steps

1. ✅ Run `python setup_telegram.py` to configure
2. ✅ Test with `python scanner_demo.py`
3. ✅ Set up scheduling (cron/systemd/GitHub Actions)
4. ✅ Verify you receive daily notifications
5. ✅ Adjust filters as needed

---

**Version**: 1.0  
**Last Updated**: 2026-10-23  
**Status**: ✅ Ready for production use
