# NSE F&O PCS Scanner - Scheduled Task Setup

## Overview

The `run_scanner_telegram.py` script is designed to run automated stock scans on a schedule and send results to Telegram.

## Quick Start

### 1. Install Dependencies

```bash
cd /home/user/nsepcs
python3 -m pip install yfinance pandas numpy plotly pytz scikit-learn scipy beautifulsoup4 openpyxl matplotlib requests
```

### 2. Configure Telegram (Optional but Recommended)

To send results to Telegram:

1. Follow instructions in `TELEGRAM_SETUP.md` to get your bot token and chat ID
2. Set environment variables:

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

### 3. Run the Scanner

```bash
python3 /home/user/nsepcs/run_scanner_telegram.py
```

## Features

✅ **Automated Stock Scanning** - Analyzes 10-20 stocks per run
✅ **Technical Analysis** - RSI, MACD, Bollinger Bands, Volume analysis
✅ **Pattern Detection** - Identifies bullish patterns and breakouts
✅ **Telegram Integration** - Sends results to your Telegram account
✅ **Local Results Storage** - Saves JSON and text reports for historical tracking
✅ **Configurable Filters** - Adjust min PCS score, volume ratios, RSI ranges

## Output Files

Results are saved to `/tmp/nsepcs_results/`:

- `scan_results_*.json` - Machine-readable results in JSON format
- `scan_report_*.txt` - Human-readable text report

## Configuration

Edit `DEFAULT_CONFIG` in `run_scanner_telegram.py`:

```python
DEFAULT_CONFIG = {
    'min_pcs_score': 55,              # Minimum quality score
    'min_volume_ratio': 1.5,          # Volume must be 1.5x average
    'liquidity_tier': 1,              # 1=highest, 3=lowest
    'max_stocks': 40,                 # Max stocks to analyze
    'pattern_strength_threshold': 65, # Min pattern strength %
    'min_rsi': 30,                    # Minimum RSI
    'max_rsi': 80,                    # Maximum RSI
}
```

## Stocks Analyzed

The scanner includes stocks from NSE F&O universe:

- **Tier 1 (Ultra High Liquidity)**: NIFTY, BANKNIFTY, RELIANCE, TCS, HDFCBANK, INFY, ICICIBANK, SBIN, LT, ITC
- Can be extended to 200+ stocks (see COMPLETE_NSE_FO_UNIVERSE in streamlit_app.py)

## Setting Up Scheduled Execution

### Using Cron (Linux/Mac)

Add to crontab:

```bash
# Run scanner every day at 3:30 PM IST (10:00 AM UTC)
30 15 * * * cd /home/user/nsepcs && python3 run_scanner_telegram.py >> /var/log/nsepcs_scanner.log 2>&1
```

### Using systemd timer (Linux)

Create `/etc/systemd/system/nsepcs-scanner.service`:

```ini
[Unit]
Description=NSE F&O PCS Scanner
After=network.target

[Service]
Type=oneshot
User=root
WorkingDirectory=/home/user/nsepcs
Environment="TELEGRAM_BOT_TOKEN=your_token"
Environment="TELEGRAM_CHAT_ID=your_chat_id"
ExecStart=/usr/bin/python3 /home/user/nsepcs/run_scanner_telegram.py
StandardOutput=journal
StandardError=journal
```

Create `/etc/systemd/system/nsepcs-scanner.timer`:

```ini
[Unit]
Description=Run NSE F&O PCS Scanner daily

[Timer]
OnCalendar=*-*-* 15:30:00  # 3:30 PM daily
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable nsepcs-scanner.timer
sudo systemctl start nsepcs-scanner.timer
sudo systemctl status nsepcs-scanner.timer
```

### Using GitHub Actions

Create `.github/workflows/stock-scanner.yml`:

```yaml
name: NSE F&O Scanner

on:
  schedule:
    - cron: '30 10 * * *'  # 10:30 AM UTC = 3:30 PM IST

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python3 run_scanner_telegram.py
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
```

## Monitoring & Logs

Check execution logs:

```bash
# View recent results
ls -lth /tmp/nsepcs_results/ | head -10

# View latest report
cat /tmp/nsepcs_results/scan_report_*.txt | tail -1

# View latest results JSON
cat /tmp/nsepcs_results/scan_results_*.json | tail -1
```

## Troubleshooting

### No data fetched from Yahoo Finance
- This is expected in sandboxed/restricted network environments
- The script falls back gracefully and saves empty results
- Works fine with unrestricted internet access

### Telegram message not sending
1. Verify bot token and chat ID are correct
2. Test manually: See TELEGRAM_SETUP.md
3. Check network connectivity

### Module not found errors
Install all dependencies:
```bash
python3 -m pip install yfinance pandas numpy plotly pytz scikit-learn scipy beautifulsoup4 openpyxl matplotlib requests
```

## Important Disclaimers

⚠️ **NOT FINANCIAL ADVICE**
- This tool is for educational and research purposes only
- Always verify results with other sources
- Options trading carries substantial risk
- Consult with qualified financial advisors before trading
- Never risk more than you can afford to lose

## Customization

### Add more stocks

Edit `TIER1_STOCKS` list:

```python
TIER1_STOCKS = [
    'NIFTY', 'BANKNIFTY', 'RELIANCE.NS', 'TCS.NS',
    # Add more symbols here
]
```

### Adjust analysis parameters

Modify `detect_simple_patterns()` method to add:
- Custom technical indicators
- Different pattern types
- Additional filters

### Change output format

Modify `format_results_for_telegram()` to customize:
- Message structure
- Emoji usage
- Information displayed

## Support

For issues:
1. Check `/tmp/nsepcs_results/` for detailed logs
2. Review error messages in script output
3. Ensure all dependencies are installed
4. Verify network connectivity for data fetching

---

**Last Updated**: 2026-10-19
**Version**: 1.0
