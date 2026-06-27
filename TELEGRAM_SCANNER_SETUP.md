# NSE Stock Scanner - Telegram Integration Guide

This guide will help you set up and run the stock scanner with Telegram integration on your local machine.

## Overview

The scanner:
- Scans NSE F&O stocks for technical patterns
- Detects breakouts, cup & handle, double bottoms, and other patterns
- Filters by volume and RSI/ADX criteria
- **Sends results directly to your Telegram** 📱
- Saves results to CSV for further analysis

## Quick Setup (5 minutes)

### Step 1: Create a Telegram Bot

1. Open Telegram and search for **`@BotFather`**
2. Send the command `/newbot`
3. Follow the prompts:
   - Give it a name (e.g., "Stock Scanner Bot")
   - Give it a username (e.g., "my_stock_scanner_bot")
4. **Copy the bot token** (looks like: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### Step 2: Get Your Chat ID

1. Open Telegram and search for **`@userinfobot`**
2. Send any message to get your user ID
3. **Copy your chat ID** (a number like `123456789`)

### Step 3: Install Dependencies

On your local machine:

```bash
# Navigate to the project directory
cd /path/to/nsepcs

# Install requirements
pip install -r requirements.txt
```

### Step 4: Set Environment Variables

```bash
# Linux/Mac
export TELEGRAM_BOT_TOKEN='paste_your_bot_token_here'
export TELEGRAM_CHAT_ID='paste_your_chat_id_here'

# Windows (Command Prompt)
set TELEGRAM_BOT_TOKEN=paste_your_bot_token_here
set TELEGRAM_CHAT_ID=paste_your_chat_id_here

# Windows (PowerShell)
$env:TELEGRAM_BOT_TOKEN='paste_your_bot_token_here'
$env:TELEGRAM_CHAT_ID='paste_your_chat_id_here'
```

### Step 5: Run the Scanner

```bash
python3 run_scanner_with_telegram.py
```

The scanner will:
1. Ask you to choose scan scope (20, 50, or all stocks)
2. Start scanning stocks
3. Display results in console
4. Save results to CSV
5. **Send results to your Telegram chat** ✅

## Understanding the Results

Each stock result shows:

- **Symbol**: Stock ticker (e.g., RELIANCE, INFY)
- **Price**: Current price in INR
- **Pattern**: Detected technical pattern (Cup & Handle, Double Bottom, etc.)
- **Strength**: Pattern strength (0-100%)
- **Confidence**: HIGH/MEDIUM/LOW based on pattern quality
- **RSI**: Relative Strength Index (overbought/oversold indicator)
- **ADX**: Average Directional Index (trend strength)
- **Volume**: Current volume vs average (multiplier)

## Example Results

### Console Output:
```
Top 10 Stocks by Strength:
────────────────────────────────────────────────────────
 1. RELIANCE      | ₹2845.50 | Current Day Breakout     |  92%
 2. INFY          | ₹1520.25 | Cup and Handle           |  88%
 3. HDFCBANK      | ₹1645.75 | Double Bottom            |  85%
```

### Telegram Message:
```
📈 NSE F&O Stock Scanner Results
Generated: 2024-06-27 14:30:00 IST
Total Stocks Scanned: 50

1. RELIANCE 🟢
   Price: ₹2845.50
   Pattern: Current Day Breakout
   Strength: 92% | Success: 78%
   RSI: 65.2 | ADX: 28.5 | Vol: 2.5x

2. INFY 🟢
   Price: ₹1520.25
   ...
```

## Filter Criteria Explained

The scanner filters stocks based on:

### 1. **Volume Filter**
- **Minimum**: Current day volume must be 1x average
- **Ideal**: 2x-3x average volume (indicates institutional interest)

### 2. **RSI (Relative Strength Index)**
- **Oversold** (< 30): Stock may bounce up
- **Normal** (30-70): Ideal range for trending
- **Overbought** (> 70): Stock may pull back

### 3. **ADX (Average Directional Index)**
- **Low** (< 20): Weak trend, choppy movement
- **Medium** (20-40): Good trend strength
- **High** (> 40): Very strong directional move

### 4. **Pattern Detection**
Detected patterns include:

- **Current Day Breakout**: Stock breaks above resistance on high volume
- **Cup and Handle**: Reversal pattern forming a cup shape
- **Double Bottom**: Two lows at same level (bullish reversal)
- **Flat Base Breakout**: Stock consolidates then breaks out
- **Head and Shoulders Bottom**: Reversal pattern (bullish)
- **Rounding Bottom**: V-shaped reversal
- **Breakout Pullback**: Initial breakout with pullback

## Advanced Usage

### Scan All 208 F&O Stocks

```bash
python3 run_scanner_with_telegram.py
# When prompted, choose option: 3 (Full scan)
```

### Scan Custom Number of Stocks

```bash
python3 run_scanner_with_telegram.py
# When prompted, choose option: 4 (Custom)
# Enter desired number (e.g., 100)
```

### Run on Schedule (Linux/Mac)

Add to crontab to run daily at 3:30 PM (after market close):

```bash
crontab -e

# Add this line:
30 15 * * 1-5 cd /path/to/nsepcs && python3 run_scanner_with_telegram.py
```

### Run on Schedule (Windows)

Use Task Scheduler:
1. Press `Win + R`, type `taskschd.msc`
2. Click "Create Basic Task"
3. Set trigger: Daily at 3:30 PM
4. Set action: `python3.exe run_scanner_with_telegram.py` in the nsepcs folder

## Troubleshooting

### "No module named 'ta'"
```bash
# Ensure the ta.py compatibility module is in the nsepcs folder
# It should be there already, but if not:
# Copy it from the repository
```

### "Failed to get ticker data"
- Check your internet connection
- Yahoo Finance might be blocked by your firewall
- Try using a VPN

### "Telegram: Failed to send message"
- Verify bot token is correct (no extra spaces)
- Verify chat ID is correct
- Check if the bot is still active (@BotFather -> /mybots)
- Ensure your machine has internet access

### "Permission denied" when running script
```bash
# Make script executable (Linux/Mac)
chmod +x run_scanner_with_telegram.py
```

## Customization

### Change Filter Criteria

Edit `run_scanner_with_telegram.py` and modify the config:

```python
config = {
    'stocks_to_scan': stocks_to_scan,
    'min_volume_ratio': 1.5,  # Change from 1.0 to 1.5 (higher = stricter)
    'show_news': True,         # Enable/disable news analysis
}
```

### Modify Telegram Message Format

Edit the `format_results_for_telegram()` function to customize:
- Number of stocks shown (change `results[:15]` to `results[:20]`)
- Message format (add emojis, change layout)
- Include additional metrics

## Data Sources

- **Stock Data**: Yahoo Finance (via yfinance)
- **Technical Indicators**: TA-Lib (via talib)
- **NSE Stocks**: 208 official NSE F&O stocks

## Performance Tips

1. **Quick Scans**: Use 20-50 stocks for fast results (2-5 minutes)
2. **Full Scans**: Use all 208 stocks for comprehensive analysis (15-30 minutes)
3. **During Market Hours**: Slower due to real-time data fetching
4. **After Market Close**: Faster (3-4 PM IST recommended)

## FAQ

**Q: Why does the scan take so long?**
A: It's fetching 3 months of data for each stock and calculating 15+ technical indicators.

**Q: Can I run this on a VPS/Server?**
A: Yes! Just set the environment variables and run it. Perfect for scheduled scans.

**Q: Will this send me duplicate messages?**
A: No, if a stock is already found, it won't be sent twice in the same scan.

**Q: Can I run this for other stock markets?**
A: Yes, modify `COMPLETE_NSE_FO_UNIVERSE` to include other symbols.

**Q: How often should I run the scanner?**
A: Recommended: Once daily after market close (3:30 PM IST)

## Support

For issues or feature requests:
1. Check the README in the main repository
2. Review the code comments for technical details
3. Test with a small scan (20 stocks) first

---

**Happy scanning! 📈**
