# NSE F&O PCS Screener - Scheduled Task Setup

## What Has Been Created

I've created a complete automation setup for running the NSE F&O PCS screener and sending results to Telegram:

### Files Created

1. **`run_final.py`** - Standalone screener script (no Streamlit dependency)
   - Analyzes stocks for technical patterns
   - Sends results to Telegram automatically
   - Minimal dependencies required

2. **`run_scanner_simple.py`** - Basic scanner version
   - Scans 15 Nifty 50 stocks for patterns
   - Lower resource usage
   - Telegram integration

3. **`run_scanner.py`** - Full comprehensive scanner
   - Scans up to 50 stocks
   - Advanced pattern detection
   - Uses the main PCS scanner logic

4. **`telegram_notifier.py`** - Telegram integration library
   - Sends messages to Telegram
   - Formats stock results
   - Error handling

5. **`setup_and_run.sh`** - Bash setup script
   - Installs dependencies
   - Verifies configuration
   - Runs the scanner

6. **`SETUP_TELEGRAM.md`** - Detailed Telegram setup guide
   - How to create Telegram bot
   - How to get chat ID
   - Configuration options

## Quick Start (Your Local Machine/Server)

### Step 1: Install Dependencies

```bash
cd /home/user/nsepcs
pip install -r requirements.txt requests
```

### Step 2: Configure Telegram

Get your credentials:
1. Chat with [@BotFather](https://t.me/botfather) on Telegram
2. Create a new bot - you'll get a token
3. Start a conversation with your bot
4. Go to: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
5. Find your Chat ID in the response

Set environment variables:
```bash
export TELEGRAM_BOT_TOKEN="123456:ABC-DEF..."
export TELEGRAM_CHAT_ID="987654321"
```

### Step 3: Run the Screener

```bash
python3 run_final.py
```

Or with the bash script:
```bash
bash setup_and_run.sh
```

## Scheduling Options

### Option A: Cron (Linux/Mac)

Schedule for 3:30 PM IST (after market close), Monday-Friday:

```bash
crontab -e
```

Add this line:
```cron
30 10 * * 1-5 cd /home/user/nsepcs && TELEGRAM_BOT_TOKEN="YOUR_TOKEN" TELEGRAM_CHAT_ID="YOUR_ID" python3 run_final.py >> /var/log/pcs_screener.log 2>&1
```

### Option B: GitHub Actions (Automated Cloud)

Create `.github/workflows/pcs-screener.yml`:

```yaml
name: PCS Screener Daily

on:
  schedule:
    - cron: '30 10 * * 1-5'  # 10:30 AM UTC = 3:30 PM IST

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install yfinance pandas numpy requests
      
      - name: Run screener
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: python3 run_final.py
```

Add secrets to GitHub:
- Settings → Secrets and variables → Actions
- Add `TELEGRAM_BOT_TOKEN`
- Add `TELEGRAM_CHAT_ID`

### Option C: Cloud Functions (AWS Lambda, Google Cloud Functions)

The `run_final.py` script is designed to work as a cloud function.

**AWS Lambda example:**
1. Upload script to Lambda
2. Set environment variables for Telegram credentials
3. Schedule with EventBridge (CloudWatch Events)
4. Trigger daily at your preferred time

### Option D: Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install yfinance pandas numpy requests
CMD ["python3", "run_final.py"]
```

Build and run:
```bash
docker build -t pcs-screener .
docker run \
  -e TELEGRAM_BOT_TOKEN="YOUR_TOKEN" \
  -e TELEGRAM_CHAT_ID="YOUR_ID" \
  pcs-screener
```

## Script Configuration

Edit the stock list in `run_final.py`:

```python
stocks = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS',  # Your stocks here
    # ... add more
]
```

Change the scan interval:
```python
data = ticker.history(period="3mo")  # Change "3mo" to "1y", "6mo", etc.
```

## How It Works

1. **Fetches data** from Yahoo Finance for the last 3 months
2. **Analyzes patterns**:
   - Volume surges
   - Resistance breakouts
   - Price momentum
   - Support/resistance levels

3. **Generates report** with:
   - Stock symbol
   - Current price
   - Volume ratio
   - Pattern type
   - Strength percentage

4. **Sends to Telegram** in a formatted message

Example Telegram output:
```
📊 NSE F&O PCS Screener
📅 2026-09-07 15:30:45 IST

✅ Found 5 stocks

INFY ₹2500.00
📊 2.5x | 📈 Resistance Breakout
💪 78%

TCS ₹3100.00
📊 1.8x | 📈 Volume Confirmation
💪 65%
```

## Monitoring

### View Logs (Cron)
```bash
tail -f /var/log/pcs_screener.log
```

### GitHub Actions
- Go to Actions tab in your GitHub repo
- View runs and their logs

### AWS Lambda CloudWatch
- Go to CloudWatch → Logs
- Search for your function name

## Troubleshooting

### "No module named 'yfinance'"
```bash
pip install yfinance pandas numpy requests
```

### "Telegram not configured"
Verify environment variables are set:
```bash
echo $TELEGRAM_BOT_TOKEN
echo $TELEGRAM_CHAT_ID
```

### "No qualifying stocks found"
- Market might be closed
- Run during market hours (9:15 AM - 3:30 PM IST, Mon-Fri)
- Check internet connection
- Verify Yahoo Finance isn't blocked

### "Failed to send to Telegram"
- Verify bot token is correct
- Verify chat ID is correct
- Make sure you've messaged the bot once
- Check internet connection

## Best Practices

✅ **DO:**
- Run after market close (3:30 PM IST) for complete day data
- Run on weekdays only (skip weekends/holidays)
- Test first with manual run before scheduling
- Keep logs for debugging
- Update stock list quarterly

❌ **DON'T:**
- Run during market hours (incomplete data)
- Run too frequently (API rate limits)
- Store credentials in code (use environment variables)
- Use the same token in multiple places

## Advanced Customization

### Change Pattern Detection

Edit the `analyze_stock()` function in `run_final.py`:

```python
# Pattern 1: Volume surge + price near resistance
if volume_ratio >= 1.5:  # Change threshold
    distance_to_high = ((high_20 - current_price) / high_20) * 100
    if distance_to_high < 3:  # Change distance
        patterns.append({...})
```

### Add More Stocks

```python
stocks = [
    # Add from these groups:
    # Nifty 50
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS',
    # Banking
    'SBIN.NS', 'ICICIBANK.NS', 'KOTAKBANK.NS',
    # IT
    'INFY.NS', 'WIPRO.NS', 'TECHM.NS',
    # Pharma
    'SUNPHARMA.NS', 'CIPLA.NS', 'DRREDDY.NS',
    # Add custom stocks...
]
```

### Change Report Format

Edit the Telegram message formatting in `send_to_telegram()` or the final message in `main()`.

## Support

For issues:
1. Check `requirements.txt` are all installed
2. Verify Telegram credentials
3. Check internet connectivity
4. Review logs for error messages
5. Test manually before scheduling

## Next Steps

1. ✅ Clone/download this repository
2. ✅ Install dependencies: `pip install -r requirements.txt requests`
3. ✅ Get Telegram credentials from BotFather
4. ✅ Set environment variables
5. ✅ Test: `python3 run_final.py`
6. ✅ Schedule using one of the options above
7. ✅ Verify first run sends Telegram message
8. ✅ Monitor logs for errors

## Questions?

- See `SETUP_TELEGRAM.md` for Telegram setup details
- See `README.md` for PCS screener algorithm details
- Check logs for error messages
- Verify all dependencies are installed

---

**Status**: ✅ Ready to deploy
**Last Updated**: 2026-09-07
