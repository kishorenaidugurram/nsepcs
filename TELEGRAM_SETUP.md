# 📱 Telegram Automation Setup Guide

This guide explains how to set up automated PCS analysis results to be sent to your Telegram account.

## Prerequisites

1. **Python 3.8+** with pip installed
2. **Telegram Bot Token** - Create a bot with [@BotFather](https://t.me/botfather) on Telegram
3. **Your Telegram Chat ID** - Get from [@userinfobot](https://t.me/userinfobot)

## Step 1: Create a Telegram Bot

1. Open Telegram and find [@BotFather](https://t.me/botfather)
2. Send: `/start`
3. Send: `/newbot`
4. Follow the prompts to create your bot
5. **Save your Bot Token** - looks like: `123456789:ABCdefGHIjklmNOPqrsTUVwxyz`

## Step 2: Get Your Chat ID

1. Open Telegram and find [@userinfobot](https://t.me/userinfobot)
2. Send: `/start`
3. **Save your Chat ID** - usually a long number like `987654321`

## Step 3: Configure Environment Variables

Add these to your shell configuration file:

```bash
# Add to ~/.bashrc or ~/.zshrc or your environment
export TELEGRAM_BOT_TOKEN='your_bot_token_here'
export TELEGRAM_CHAT_ID='your_chat_id_here'
```

Then reload: `source ~/.bashrc`

Alternatively, set them before running:

```bash
export TELEGRAM_BOT_TOKEN='your_bot_token_here'
export TELEGRAM_CHAT_ID='your_chat_id_here'
python3 run_analysis.py
```

## Step 4: Install Dependencies

```bash
cd /home/user/nsepcs
pip3 install -r requirements.txt
```

## Step 5: Run the Analysis

```bash
python3 run_analysis.py
```

This will:
- Scan all NSE F&O stocks
- Find stocks meeting filter criteria (minimum 70% pattern strength)
- Send results to your Telegram
- Save results to CSV

## Step 6: Schedule Automatic Runs (Optional)

### Using Cron (Linux/Mac)

Edit your crontab:
```bash
crontab -e
```

Add this line to run analysis every day at 3:30 PM IST:
```bash
30 15 * * * export TELEGRAM_BOT_TOKEN='your_token'; export TELEGRAM_CHAT_ID='your_id'; cd /home/user/nsepcs && python3 run_analysis.py >> /var/log/pcs_scan.log 2>&1
```

Or better, create a shell script:

```bash
# Create ~/bin/run_pcs_scan.sh
#!/bin/bash
export TELEGRAM_BOT_TOKEN='your_bot_token_here'
export TELEGRAM_CHAT_ID='your_chat_id_here'
cd /home/user/nsepcs
python3 run_analysis.py >> /var/log/pcs_scan.log 2>&1
```

Then in crontab:
```bash
30 15 * * * ~/bin/run_pcs_scan.sh
```

### Using systemd Timer (More Reliable)

Create `/etc/systemd/system/pcs-scan.service`:
```ini
[Unit]
Description=NSE F&O PCS Scanner
After=network.target

[Service]
Type=oneshot
User=your_username
Environment="TELEGRAM_BOT_TOKEN=your_bot_token"
Environment="TELEGRAM_CHAT_ID=your_chat_id"
WorkingDirectory=/home/user/nsepcs
ExecStart=/usr/bin/python3 /home/user/nsepcs/run_analysis.py
```

Create `/etc/systemd/system/pcs-scan.timer`:
```ini
[Unit]
Description=Run PCS Scan Daily at 3:30 PM
Requires=pcs-scan.service

[Timer]
OnCalendar=*-*-* 15:30:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable pcs-scan.timer
sudo systemctl start pcs-scan.timer
```

Check status:
```bash
sudo systemctl status pcs-scan.timer
sudo systemctl list-timers pcs-scan.timer
```

## Customization

### Adjust Filter Criteria

Edit `run_analysis.py`, line ~180:

```python
results, total_scanned = run_analysis(
    min_pattern_strength=70,      # Change this: 70 = stricter, 60 = more results
    max_stocks=None,               # Change to limit scan (e.g., 50)
    focus_high_confidence=False    # Set to True for only HIGH confidence stocks
)
```

### Different Schedule

Edit cron or timer schedule:
- `0 9 * * *` = 9:00 AM
- `15 15 * * 1-5` = 3:15 PM on weekdays only
- `*/30 * * * *` = Every 30 minutes

## Troubleshooting

### "ModuleNotFoundError: No module named 'pandas'"

```bash
pip3 install --upgrade pandas numpy yfinance ta requests
```

### "Connection timeout" or API errors

- Check internet connection
- Verify Telegram token is correct
- Check if Telegram bot token has expired (rare)

### "Chat ID invalid"

- Verify you got the Chat ID from [@userinfobot](https://t.me/userinfobot)
- Make sure you send the bot at least one message first

### Script takes too long

Edit `run_analysis.py` and reduce `max_stocks`:
```python
results, total_scanned = run_analysis(
    min_pattern_strength=70,
    max_stocks=50,  # Scan only 50 stocks instead of all
    focus_high_confidence=True  # Only HIGH confidence
)
```

## Example Telegram Output

```
📊 PCS Analysis Results

Scanned: 219 stocks
Found: 12 stocks

🟢 HIGH Confidence
• RELIANCE   - 92% | ₹2850.25 | RSI: 65
• TCS        - 88% | ₹3450.50 | RSI: 62
  ... and 2 more

🟡 MEDIUM Confidence
• HDFCBANK   - 76%
  ... and 7 more

━━━━━━━━━━━━━━━━━━━━━━━
View full analysis: [PCS Screener Link]
```

## Support

For issues:
1. Check logs: `tail -f /var/log/pcs_scan.log`
2. Run manually to see errors: `python3 run_analysis.py`
3. Test Telegram connection: `python3 telegram_notifier.py`

## Next Steps

1. Run once manually: `python3 run_analysis.py`
2. Verify you receive the Telegram message
3. Set up automatic scheduling
4. Monitor logs for any issues
