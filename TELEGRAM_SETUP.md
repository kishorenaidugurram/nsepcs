# NSE PCS Scanner - Telegram Integration Setup

## Overview
The scanner has been configured to send stock screening results directly to Telegram. This allows you to receive PCS (Put Credit Spreads) pattern alerts on your phone automatically.

## Quick Start

### 1. Create a Telegram Bot
1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow the prompts
3. You'll receive a **BOT TOKEN** (looks like: `123456789:ABCDefGHIjklMNOpqrSTUvwxyz`)
4. Save this token securely

### 2. Get Your Chat ID
1. Open Telegram and search for `@userinfobot`
2. Send any message to it
3. It will reply with your **CHAT ID** (usually a number like: `123456789`)
4. Or message your bot and visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`

### 3. Set Environment Variables
Set these environment variables in your system or container:

```bash
export TELEGRAM_BOT_TOKEN='123456789:ABCDefGHIjklMNOpqrSTUvwxyz'
export TELEGRAM_CHAT_ID='123456789'
```

For Docker/Kubernetes, add to your environment configuration:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

## Running the Scanner

### Option 1: Simple Scanner (Lightweight)
```bash
python3 /home/user/nsepcs/simple_scanner.py
```

**Features:**
- Minimal dependencies
- Sends formatted report to Telegram
- Shows sample results if Telegram not configured
- Fast execution

**Output:** HTML-formatted message in Telegram with:
- Number of qualifying stocks
- Top breakout patterns detected
- Pattern strength metrics
- Filter criteria applied

### Option 2: Full Scanner (Coming Soon)
```bash
python3 /home/user/nsepcs/run_scanner_telegram.py
```

**Features:**
- Deep technical analysis (PCS patterns)
- CSV export of results
- Weekly timeframe validation
- Enhancement analysis (delivery volume, F&O consolidation)
- News sentiment integration

## Scheduled Execution

To run the scanner on a schedule (e.g., daily at market close):

### Using Cron
```bash
# Add to crontab (crontab -e)
# Run at 4:00 PM IST (after market close)
0 16 * * 1-5 cd /home/user/nsepcs && TELEGRAM_BOT_TOKEN='your_token' TELEGRAM_CHAT_ID='your_chat_id' python3 simple_scanner.py
```

### Using Systemd Timer
Create `/etc/systemd/system/nsepcs-telegram.service`:
```ini
[Unit]
Description=NSE PCS Scanner Telegram Reporter
After=network.target

[Service]
Type=oneshot
User=root
WorkingDirectory=/home/user/nsepcs
Environment="TELEGRAM_BOT_TOKEN=your_token"
Environment="TELEGRAM_CHAT_ID=your_chat_id"
ExecStart=/usr/bin/python3 simple_scanner.py
```

Create `/etc/systemd/system/nsepcs-telegram.timer`:
```ini
[Unit]
Description=Run NSE PCS Scanner daily

[Timer]
OnCalendar=*-*-* 16:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Then enable:
```bash
systemctl enable nsepcs-telegram.timer
systemctl start nsepcs-telegram.timer
```

## Telegram Message Format

The scanner sends a formatted HTML message with:

```
🔍 NSE PCS Scanner Report
📅 2026-10-29 16:30 IST

📊 Summary:
  • Total Qualifying Stocks: 6
  • Total Patterns: 8

📈 Top Stocks:
1. INFY - Current Day Breakout - 82% Strength
2. ICICIBANK - Current Day Breakout - 78% Strength
... and more

Filter Applied:
RSI: 30-75 | ADX: 20+ | Vol: 1.2x | Strength: 65%+
```

## Filter Criteria

The scanner uses these default filters:

| Parameter | Value | Description |
|-----------|-------|-------------|
| RSI Range | 30-75 | Relative Strength Index |
| ADX Min | 20 | Average Directional Index (trend strength) |
| Volume Ratio | 1.2x | Current volume vs 20-day average |
| Pattern Strength | 65% | Minimum pattern confidence score |
| Lookback | 20 days | Historical period for analysis |
| Stocks | NSE F&O (208) | Focus on highly liquid stocks |

## Patterns Detected

The scanner identifies these PCS-suitable patterns:

1. **Current Day Breakout** - Real-time EOD confirmation
2. **Cup with Handle** - William O'Neil IBD pattern
3. **Flat Base** - Mark Minervini pattern
4. **Rectangle Bottom** - Classical consolidation breakout
5. **Head and Shoulders Bottom** - Reversal pattern
6. **Double Bottom** - Support validation
7. **And 6 more patterns...**

## Troubleshooting

### Message not received?

1. **Check Telegram credentials:**
   ```bash
   python3 -c "import os; print(f\"Token: {os.getenv('TELEGRAM_BOT_TOKEN')}\")"
   ```

2. **Verify bot is active:**
   - Message your bot on Telegram first
   - Check if bot permissions are correct

3. **Test connection:**
   ```bash
   # This should return OK if config is correct
   python3 simple_scanner.py
   ```

4. **Check Telegram API status:**
   ```bash
   curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe
   ```

## Next Steps

1. **Get Telegram credentials** (steps above)
2. **Export environment variables:**
   ```bash
   export TELEGRAM_BOT_TOKEN='your_token'
   export TELEGRAM_CHAT_ID='your_chat_id'
   ```
3. **Test the scanner:**
   ```bash
   python3 simple_scanner.py
   ```
4. **Set up scheduled execution** (cron or systemd)
5. **Receive daily PCS pattern alerts!**

## Advanced Configuration

### Custom Filter Thresholds
Edit `simple_scanner.py` and modify:
```python
'rsi_min': 30,      # Minimum RSI
'rsi_max': 75,      # Maximum RSI
'adx_min': 20,      # Minimum ADX
'min_volume_ratio': 1.2,  # Volume requirement
'pattern_strength_min': 65,  # Pattern strength %
```

### Custom Stock Universe
Modify the `NSE_FO_STOCKS` list in `simple_scanner.py` to scan specific stocks or sectors.

## Support

For issues or enhancements:
1. Check the error messages in stdout/stderr
2. Review Telegram API documentation: https://core.telegram.org/bots/api
3. Verify network connectivity to api.telegram.org

## Security Notes

- Never commit your TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID to git
- Use environment variables or secure vaults for credentials
- Rotate bot tokens if compromised
- Monitor bot usage for suspicious activity

---
**Last Updated:** 2026-10-29
**Scanner Version:** v1.0 (Simple/Lightweight)
