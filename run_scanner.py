#!/usr/bin/env python3
"""
NSE F&O PCS Screener - Simplified Telegram Integration
Runs basic technical analysis on F&O stocks and sends results
"""

import os
import sys
import json
from datetime import datetime, timedelta
import requests
import warnings

warnings.filterwarnings('ignore')

# Get Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
DRY_RUN = os.getenv('TELEGRAM_DRY_RUN', 'false').lower() == 'true'

# Try loading from config file if env vars not set
if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    config_file = os.path.expanduser("~/.nsepcs_telegram.json")
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                TELEGRAM_BOT_TOKEN = config.get('token')
                TELEGRAM_CHAT_ID = config.get('chat_id')
        except Exception as e:
            pass

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("ℹ️  Running in DRY-RUN mode (no Telegram credentials found)")
    print("To enable Telegram notifications, run: python setup_telegram.py\n")
    DRY_RUN = True


def send_telegram_message(message: str) -> bool:
    """Send message to Telegram"""
    if DRY_RUN:
        print("=" * 70)
        print("📱 [DRY-RUN] Telegram Message:")
        print("=" * 70)
        print(message)
        print("=" * 70)
        return True

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        response = requests.post(url, data=data, timeout=10)
        success = response.status_code == 200
        if success:
            print("✅ Message sent to Telegram successfully!")
        else:
            print(f"❌ Failed to send message. Status: {response.status_code}")
        return success
    except Exception as e:
        print(f"❌ Error sending Telegram message: {e}")
        return False


def fetch_stock_data(symbol: str) -> dict:
    """Fetch stock data from Yahoo Finance"""
    try:
        import yfinance as yf
    except ImportError:
        print(f"⚠️  yfinance not installed. Skipping {symbol}")
        return None

    try:
        # Add .NS suffix for NSE stocks
        ticker = f"{symbol}.NS" if not symbol.endswith('.NS') else symbol
        stock = yf.Ticker(ticker)

        # Get last 60 days of data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)

        data = stock.history(start=start_date.strftime('%Y-%m-%d'),
                            end=end_date.strftime('%Y-%m-%d'))

        if data.empty or len(data) < 20:
            return None

        # Get current price info
        last_row = data.iloc[-1]
        prev_row = data.iloc[-2] if len(data) > 1 else last_row

        current_price = last_row['Close']
        prev_price = prev_row['Close']
        change_pct = ((current_price - prev_price) / prev_price * 100) if prev_price else 0

        # Calculate simple technical indicators
        close_prices = data['Close'].values
        high_prices = data['High'].values
        low_prices = data['Low'].values

        # RSI calculation (simplified)
        def calc_rsi(prices, period=14):
            if len(prices) < period + 1:
                return 50
            deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
            seed = deltas[:period]
            up = [d for d in seed if d >= 0]
            down = [d for d in seed if d < 0]

            rs = len(up) / len(down) if down else 1.0
            rsi = 100.0 - 100.0 / (1.0 + rs)
            return rsi

        rsi = calc_rsi(close_prices)

        # Simple support detection (low of last 20 days)
        support = low_prices[-20:].min()
        resistance = high_prices[-20:].max()

        # Volume analysis
        volumes = data['Volume'].values
        avg_volume = volumes[-20:].mean() if len(volumes) > 20 else volumes.mean()
        current_volume = volumes[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0

        return {
            'symbol': symbol,
            'price': float(current_price),
            'change_pct': float(change_pct),
            'rsi': float(rsi),
            'support': float(support),
            'resistance': float(resistance),
            'volume_ratio': float(volume_ratio),
            'avg_volume': float(avg_volume),
            'current_volume': float(current_volume),
        }
    except Exception as e:
        print(f"⚠️  Error fetching data for {symbol}: {str(e)[:50]}")
        return None


def analyze_stocks(stocks_list: list, filters: dict = None) -> list:
    """Analyze stocks and return those meeting criteria"""

    if filters is None:
        filters = {
            'rsi_min': 30,
            'rsi_max': 75,
            'min_volume_ratio': 0.8,
        }

    qualifying = []

    print(f"\n📊 Scanning {len(stocks_list)} stocks...")
    print(f"Filters: RSI({filters['rsi_min']}-{filters['rsi_max']}), Volume Ratio(>{filters['min_volume_ratio']})\n")

    for symbol in stocks_list:
        print(f"  Checking {symbol}...", end='', flush=True)
        data = fetch_stock_data(symbol)

        if data is None:
            print(" ⚠️  No data")
            continue

        # Check filter criteria
        meets_criteria = (
            filters['rsi_min'] <= data['rsi'] <= filters['rsi_max'] and
            data['volume_ratio'] >= filters['min_volume_ratio']
        )

        if meets_criteria:
            print(f" ✅ (RSI: {data['rsi']:.1f}, Price: ₹{data['price']:.2f})")
            qualifying.append(data)
        else:
            print(f" ❌")

    # Sort by RSI proximity to middle (45-65 is sweet spot)
    def rsi_score(data):
        sweet_spot = 55
        return -abs(data['rsi'] - sweet_spot)

    qualifying.sort(key=rsi_score, reverse=True)
    return qualifying


def format_message(qualifying_stocks: list) -> str:
    """Format results as Telegram message"""
    if not qualifying_stocks:
        return "❌ <b>No stocks met the filter criteria today.</b>\n\n⚠️ <i>Try adjusting your filters.</i>"

    from datetime import datetime
    import pytz

    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist).strftime("%Y-%m-%d %H:%M %Z")

    message = f"""🚀 <b>NSE F&O PCS Scanner Results</b>
📅 <i>{current_time}</i>

✅ <b>Stocks Meeting Criteria: {len(qualifying_stocks)}</b>

"""

    for i, stock in enumerate(qualifying_stocks[:10], 1):
        change_sign = "+" if stock['change_pct'] >= 0 else ""
        change_color = "🟢" if stock['change_pct'] >= 0 else "🔴"

        message += f"""<b>{i}. {stock['symbol']}</b>
   💰 <code>₹{stock['price']:.2f}</code> {change_color} {change_sign}{stock['change_pct']:.2f}%
   📊 RSI: {stock['rsi']:.1f} | Support: ₹{stock['support']:.2f}
   📈 Volume Ratio: {stock['volume_ratio']:.2f}x

"""

    if len(qualifying_stocks) > 10:
        message += f"<i>... and {len(qualifying_stocks) - 10} more stocks</i>\n"

    message += """
<b>📋 Filter Criteria Used:</b>
   • RSI: 30-75
   • Volume Ratio: >0.8x

⚠️ <i>Disclaimer: For educational use only. Not financial advice. Always DYOR before trading.</i>
"""

    return message


def main():
    """Main execution"""
    print("=" * 70)
    print("🚀 NSE F&O PCS Scanner - Telegram Automation")
    print("=" * 70)

    # List of F&O stocks to scan
    stocks = [
        # Tier 1 - Ultra High Liquidity
        'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'SBIN', 'LT', 'ITC',
        # Tier 2 - High Liquidity
        'KOTAKBANK', 'AXISBANK', 'HCLTECH', 'WIPRO', 'MARUTI', 'ASIANPAINT',
        'BHARTIARTL', 'SUNPHARMA', 'TATAMOTORS', 'ADANIENT',
        # Tier 3 - Medium Liquidity
        'BAJFINANCE', 'BAJAJFINSV', 'INDUSINDBK', 'TECHM', 'TITAN', 'NESTLEIND',
        'ULTRACEMCO', 'POWERGRID', 'NTPC', 'ONGC', 'COALINDIA', 'JSWSTEEL',
        'TATASTEEL', 'HINDALCO'
    ]

    # Analyze stocks
    qualifying = analyze_stocks(stocks)

    # Format and send message
    message = format_message(qualifying)

    print("\n" + "=" * 70)
    print(f"📊 Result: Found {len(qualifying)} qualifying stocks")
    print("=" * 70)

    # Send to Telegram
    print("\n📤 Sending results...")
    success = send_telegram_message(message)

    return 0 if success else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        error_msg = f"🔴 <b>Scanner Error</b>\n\n<code>{str(e)[:200]}</code>"
        send_telegram_message(error_msg)
        sys.exit(1)
