# NSE PCS Scanner - Telegram Integration

Automated scanner to identify NSE F&O stocks meeting PCS (Put Credit Spread) trading criteria and send results to Telegram.

## Setup

### 1. Telegram Bot Configuration

Create a Telegram bot and get credentials:

1. **Create a bot on Telegram:**
   - Open Telegram and search for `@BotFather`
   - Send `/newbot` command
   - Follow the prompts to create your bot
   - Copy the **Bot Token** provided (format: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

2. **Get your Telegram Chat ID:**
   - Start a conversation with your new bot
   - Send any message
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Look for the `chat.id` in the response
   - This is your **Chat ID**

### 2. Set Environment Variables

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

Or create a `.env` file:

```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

Then source it:

```bash
source .env
```

## Running the Scanner

### Option 1: Demo Mode (Simulated Data - Always Works)

```bash
python3 scanner_telegram.py
```

This generates realistic sample data and sends results to Telegram (if configured).

**Output:**
- Displays top stocks with technical indicators
- Sends formatted message to Telegram
- Shows patterns detected (Bullish Trend, Volume Increase, Near Support, etc.)

### Option 2: Live Data Mode (When Internet Available)

Use the full Streamlit app:

```bash
streamlit run streamlit_app.py
```

## Features

### Pattern Detection
The scanner detects the following bullish patterns:

1. **Bullish Trend** - Price above moving averages with strong ADX
2. **Near Support** - Price near recent lows with low RSI (oversold)
3. **Volume Increase** - Volume surge indicating institutional interest  
4. **Strong Trend** - ADX > 25 indicating directional strength
5. **Oversold Bounce** - RSI < 35 potential reversal opportunity

### Technical Indicators Used
- **RSI** (Relative Strength Index) - Overbought/Oversold levels
- **ADX** (Average Directional Index) - Trend strength
- **Volume Ratio** - Current vs average volume comparison
- **Moving Averages** - Trend direction

### Telegram Message Format

```
🔍 NSE PCS Scanner - Daily Results
(Demo Mode - Simulated Data)

📊 Found 20 stocks meeting criteria:

1. TATASTEEL - ₹181.87
   📈 RSI: 56 | ADX: 29
   🎯 Bullish Trend (199%)

... (up to 10 stocks shown)

⏰ Scan: 2026-11-05 09:20 IST
```

## Stocks Monitored

The scanner covers **208 NSE F&O stocks** including:

### Tier 1 - Ultra High Liquidity
- RELIANCE, TCS, HDFCBANK, INFY, ICICIBANK, SBIN, LT, ITC

### Tier 2 - High Liquidity  
- KOTAKBANK, AXISBANK, HCLTECH, WIPRO, MARUTI, ASIANPAINT, BHARTIARTL, SUNPHARMA, TATAMOTORS, ADANIENT

### Tier 3 - Medium Liquidity
- BAJFINANCE, BAJAJFINSV, INDUSINDBK, TECHM, TITAN, NESTLEIND, ULTRACEMCO, POWERGRID, NTPC, ONGC, COALINDIA, JSWSTEEL, TATASTEEL, HINDALCO, and others...

## Scheduling (Optional)

### Linux/Mac - Crontab

Run daily at 3:30 PM IST (after market close):

```bash
30 15 * * 1-5 cd /home/user/nsepcs && TELEGRAM_BOT_TOKEN=your_token TELEGRAM_CHAT_ID=your_id python3 scanner_telegram.py >> /var/log/nse_scanner.log 2>&1
```

### Docker / Kubernetes

```bash
docker run -e TELEGRAM_BOT_TOKEN=your_token \
           -e TELEGRAM_CHAT_ID=your_id \
           -v /home/user/nsepcs:/app \
           python:3.11 \
           python3 /app/scanner_telegram.py
```

## Interpretation Guide

### Pattern Strength Levels

- **High (75-100%)** - Strong pattern confirmation
- **Medium (60-74%)** - Moderate pattern reliability  
- **Low (40-59%)** - Emerging patterns, less reliable

### RSI Interpretation

- **30-40** - Oversold, potential bounce opportunities
- **40-60** - Neutral zone
- **60-70** - Strong momentum, overbought risk
- **>70** - Overbought, reversal risk

### ADX Interpretation

- **<20** - Weak trend, consolidation
- **20-25** - Moderate trend strength
- **>25** - Strong directional trend

## Troubleshooting

### No message sent to Telegram

**Check 1:** Verify credentials are correct
```bash
echo $TELEGRAM_BOT_TOKEN
echo $TELEGRAM_CHAT_ID
```

**Check 2:** Test bot directly
```bash
curl -X POST https://api.telegram.org/bot{TOKEN}/sendMessage \
  -d chat_id={CHAT_ID} \
  -d text="Test message"
```

**Check 3:** Check network connectivity
- Ensure your environment allows HTTPS outbound connections
- Test with: `curl -I https://api.telegram.org`

### No stocks found

- Market may be closed
- Adjust RSI and ADX filters in the code
- Reduce pattern strength minimum (default: 65%)

## Advanced Usage

### Custom Stock List

Edit the `SAMPLE_STOCKS` dictionary in `scanner_telegram.py`:

```python
SAMPLE_STOCKS = {
    'YOURSTOCK': {'base_price': 1000, 'volatility': 0.02, 'trend': 0.005},
    # Add more stocks...
}
```

### Adjust Filter Sensitivity

Modify these parameters in `demo_scanner.py`:

```python
# More lenient - finds more patterns
rsi_range = (20, 80)      # Default: (30, 70)
min_adx = 15              # Default: 20
min_patterns = 1          # Default: 2

# More strict - only high-quality patterns
rsi_range = (40, 65)      # Tighter range
min_adx = 25              # Requires stronger trend
min_patterns = 2          # Multiple patterns needed
```

## Disclaimer

**This is for educational and informational purposes only.**

- Past performance does not guarantee future results
- Always conduct your own research before trading
- Consult with financial advisors
- Paper trade first before live implementation
- Options trading involves substantial risk

## Support

For issues or feature requests, check the main [README.md](./README.md) or the Streamlit app interface.

---

**Happy Trading! 📈**
