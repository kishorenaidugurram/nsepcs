# Telegram Integration - NSE F&O Stock Scanner

## Overview

The NSE F&O Stock Scanner now includes Telegram integration to send scan results directly to your Telegram chat. Results are automatically formatted and sent at the end of each scan.

## Setup Instructions

### 1. Create a Telegram Bot

1. Open Telegram and find **@BotFather**
2. Send `/start` and follow the instructions
3. Send `/newbot` to create a new bot
4. Give it a name and username
5. **Save the Bot Token** (looks like: `123456789:ABCdefGHIjklmnopQRSTuvwxyzABCDEfgh`)

### 2. Get Your Telegram Chat ID

**Option A: Direct Chat**
1. Send any message to your bot
2. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Replace `<YOUR_BOT_TOKEN>` with your actual bot token
4. Look for `"chat":{"id":123456789,...}`
5. Your chat ID is that number

**Option B: Using a Bot**
1. Find **@userinfobot** on Telegram
2. Send `/start` and it will show your user ID
3. Start your bot and send a message
4. Use the user ID as your chat ID

### 3. Configure Environment Variables

Set the following environment variables:

```bash
export TELEGRAM_BOT_TOKEN='your_bot_token_here'
export TELEGRAM_CHAT_ID='your_chat_id_here'
```

**Permanent Setup (add to `~/.bashrc` or `~/.zshrc`):**

```bash
echo "export TELEGRAM_BOT_TOKEN='your_token'" >> ~/.bashrc
echo "export TELEGRAM_CHAT_ID='your_chat_id'" >> ~/.bashrc
source ~/.bashrc
```

## Running the Scanner

### Option 1: Standalone Scanner (Recommended)

Uses minimal dependencies and runs independently:

```bash
python3 standalone_scanner.py
```

**First time setup:**
```bash
pip install pandas numpy yfinance ta requests python-telegram-bot
python3 standalone_scanner.py
```

### Option 2: Full-Featured Scanner

Uses the complete Streamlit app's scanning logic:

```bash
pip install -r requirements.txt
python3 telegram_scanner.py --limit 50 --strength 70
```

### Command Line Options

```
--token TEXT           Telegram Bot Token (or use TELEGRAM_BOT_TOKEN env var)
--chat-id TEXT         Telegram Chat ID (or use TELEGRAM_CHAT_ID env var)
--limit INTEGER        Number of stocks to scan (default: 50)
--strength INTEGER     Minimum pattern strength (default: 70)
```

## Scheduled Execution

### Using Cron (Linux/Mac)

1. Edit crontab: `crontab -e`
2. Add a schedule (e.g., 5 minutes after market close):

```cron
# Run scanner at 3:35 PM (IST market closes at 3:30 PM)
35 15 * * 1-5 cd /home/user/nsepcs && python3 standalone_scanner.py

# Or at 9 AM every day
0 9 * * 1-5 cd /home/user/nsepcs && python3 standalone_scanner.py
```

### Using GitHub Actions

Create `.github/workflows/stock-scanner.yml`:

```yaml
name: NSE Stock Scanner

on:
  schedule:
    - cron: '35 10 * * 1-5'  # 4:05 PM IST (10:35 UTC)

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install pandas numpy yfinance ta requests python-telegram-bot
      - name: Run scanner
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: python3 standalone_scanner.py
```

## Message Format

Results are sent in the following format:

```
📊 Scan Results - X Stocks Found
[Timestamp]

1. STOCK1 | ₹Price | Strength: XX%
   RSI: XX | ADX: XX | Vol: XXx
   Patterns: Pattern1, Pattern2

2. STOCK2 | ₹Price | Strength: XX%
   ...

✅ Scan Complete
Total: X stocks
Time: [Timestamp]
```

## Scanner Configuration

### Default Filter Settings

- **RSI Range**: 30-85 (momentum strength)
- **Minimum ADX**: 15 (trend strength)
- **Volume Ratio**: 1.0x (minimum volume threshold)
- **Pattern Strength**: 70% (minimum pattern score)

### Pattern Types Detected

- Current Day Breakout (Priority)
- Cup and Handle
- Double Bottom
- Flat Base
- Bump and Run
- Rectangle Bottom
- Head & Shoulders Bottom
- Rounding Bottom
- Inverted Scallop
- Three Rising Valleys

### Customization

Edit the filter values in `standalone_scanner.py`:

```python
# In the scan_stock() function
if not (30 <= rsi <= 85) or adx < 15:  # Adjust these thresholds
    return None
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'pandas'"

Install dependencies:
```bash
pip install -r requirements.txt
```

### "Telegram error: Unauthorized"

Check your bot token and chat ID:
```bash
python3 -c "
import os
print('Bot Token:', os.getenv('TELEGRAM_BOT_TOKEN'))
print('Chat ID:', os.getenv('TELEGRAM_CHAT_ID'))
"
```

### No message received

1. Verify bot token and chat ID are correct
2. Test the bot: `curl https://api.telegram.org/bot<TOKEN>/sendMessage?chat_id=<ID>&text=Test`
3. Check network connectivity
4. Ensure bot has permission to send messages

### Scanner too slow

Reduce the number of stocks:
```bash
python3 standalone_scanner.py  # Scans only 100 stocks
```

Or modify the scan limit in the script.

## Results Storage

Scan results are also saved locally:

- **Path**: `/tmp/scan_results_YYYYMMDD_HHMMSS.json`
- **Format**: JSON with full pattern details
- **Usage**: For further analysis or record-keeping

## Performance Tips

1. **Reduce stock count**: Scan fewer stocks for faster results
2. **Adjust strength threshold**: Lower values find more patterns
3. **Run off-peak**: Execute after market hours
4. **Use threading**: Scanner uses 10 concurrent threads by default

## Support

For issues or feature requests, check:
- Telegram bot logs
- Scanner output in terminal
- JSON results file for detailed data

## Security

⚠️ **Important**: 
- Never commit `TELEGRAM_BOT_TOKEN` or `TELEGRAM_CHAT_ID` to git
- Use environment variables or secret management
- Store credentials securely
- Rotate bot tokens if exposed
