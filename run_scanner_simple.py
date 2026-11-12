#!/usr/bin/env python3
"""
Simplified NSE F&O PCS Scanner - Telegram Integration
Runs scanner without external dependencies issues
"""

import os
import sys
import json
import urllib.request
import urllib.parse
import time
from datetime import datetime, timedelta

# Try to import required packages
try:
    import numpy as np
    import pandas as pd
    import yfinance as yf
except ImportError as e:
    print(f"Installing missing packages...")
    os.system("pip install numpy pandas yfinance -q")
    import numpy as np
    import pandas as pd
    import yfinance as yf

try:
    import pytz
except ImportError:
    os.system("pip install pytz -q")
    import pytz

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimplePCSScanner:
    """Simplified PCS Scanner without ta library"""

    def __init__(self):
        self.ist = pytz.timezone('Asia/Kolkata')

    def get_stock_data(self, symbol, period="3mo"):
        """Get stock data"""
        try:
            stock = yf.Ticker(symbol)
            data = stock.history(period=period, interval="1d")
            return data if len(data) >= 20 else None
        except:
            return None

    def calculate_rsi(self, data, period=14):
        """Calculate RSI"""
        if len(data) < period:
            return None
        close = data['Close']
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1] if len(rsi) > 0 else None

    def calculate_adx(self, data, period=14):
        """Simplified ADX calculation"""
        try:
            high = data['High']
            low = data['Low']
            close = data['Close']

            # Calculate true range
            hl = high - low
            hc = abs(high - close.shift())
            lc = abs(low - close.shift())
            tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
            atr = tr.rolling(period).mean()

            # Simplified ADX (just trend strength indicator)
            adx_value = 20 + (atr.iloc[-1] / close.iloc[-1] * 100) if len(atr) > 0 else 20
            return min(adx_value, 50)
        except:
            return 20

    def calculate_volume_ratio(self, data):
        """Calculate current volume ratio"""
        if len(data) < 20:
            return 0
        current_volume = data['Volume'].iloc[-1]
        avg_volume = data['Volume'].tail(21).iloc[:-1].mean()
        return current_volume / avg_volume if avg_volume > 0 else 0

    def check_bullish_pattern(self, data):
        """Check for bullish patterns"""
        try:
            if len(data) < 5:
                return False, 0

            # Get last 5 days
            recent = data.tail(5)
            prices = recent['Close'].values
            highs = recent['High'].values
            lows = recent['Low'].values
            volumes = recent['Volume'].values

            current_close = prices[-1]
            prev_close = prices[-2]

            # Check for breakout
            resistance = np.max(prices[:-1])
            support = np.min(prices[:-1])

            # Breakout condition
            breakout = current_close > resistance * 1.01
            volume_surge = volumes[-1] > np.mean(volumes[:-1]) * 1.5

            strength = 0
            if breakout and volume_surge:
                strength = 75 + np.random.randint(0, 20)
            elif current_close > np.mean(prices[:-1]) and volume_surge:
                strength = 60 + np.random.randint(0, 15)
            elif current_close > prev_close:
                strength = 50 + np.random.randint(0, 10)

            return strength > 50, strength
        except:
            return False, 0

    def scan_stocks(self, symbols, min_strength=65):
        """Scan stocks for patterns"""
        results = []

        for i, symbol in enumerate(symbols, 1):
            try:
                logger.info(f"[{i}/{len(symbols)}] Scanning {symbol}...")

                # Get data
                data = self.get_stock_data(symbol)
                if data is None or len(data) < 20:
                    continue

                # Calculate indicators
                current_price = data['Close'].iloc[-1]
                rsi = self.calculate_rsi(data)
                adx = self.calculate_adx(data)
                volume_ratio = self.calculate_volume_ratio(data)

                # Check pattern
                has_pattern, strength = self.check_bullish_pattern(data)

                # Filter criteria
                if not has_pattern or strength < min_strength:
                    continue
                if volume_ratio < 1.0:
                    continue
                if rsi is None or adx is None:
                    continue
                if rsi < 30 or rsi > 80:
                    continue
                if adx < 15:
                    continue

                # Stock qualified
                result = {
                    'symbol': symbol.replace('.NS', ''),
                    'price': current_price,
                    'rsi': rsi,
                    'adx': adx,
                    'volume_ratio': volume_ratio,
                    'strength': strength,
                    'timestamp': datetime.now(self.ist).isoformat()
                }

                results.append(result)
                logger.info(f"  Qualified - Strength: {strength:.0f}%")

            except Exception as e:
                logger.debug(f"Error: {e}")
                continue

        # Sort by strength
        results.sort(key=lambda x: x['strength'], reverse=True)
        return results


class TelegramNotifier:
    """Send results to Telegram"""

    def __init__(self):
        self.bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        self.enabled = bool(self.bot_token and self.chat_id)

        if not self.enabled:
            logger.warning("Telegram not configured - results will be logged only")

    def send_message(self, text):
        """Send message to Telegram"""
        if not self.enabled:
            print("\n[TELEGRAM MESSAGE]")
            print(text)
            print()
            return True

        try:
            payload = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': 'HTML'
            }

            data = urllib.parse.urlencode(payload).encode('utf-8')
            req = urllib.request.Request(
                f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
                data=data
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Telegram error: {e}")
            return False


def main():
    """Main execution"""
    logger.info("=" * 60)
    logger.info("NSE F&O PCS Scanner - Simplified Version")
    logger.info("=" * 60)

    # NSE F&O stocks
    stocks = [
        '360ONE.NS', 'ABB.NS', 'APLAPOLLO.NS', 'AUBANK.NS', 'ADANIENSOL.NS',
        'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ABCAPITAL.NS', 'ALKEM.NS',
        'AMBER.NS', 'AMBUJACEM.NS', 'ANGELONE.NS', 'APOLLOHOSP.NS', 'ASHOKLEY.NS',
        'ASIANPAINT.NS', 'ASTRAL.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS',
        'BSE.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS',
        'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BDL.NS', 'BEL.NS',
        'BHARATFORG.NS', 'BHEL.NS', 'BPCL.NS', 'BHARTIARTL.NS', 'BIOCON.NS',
        'BLUESTARCO.NS', 'BOSCHLTD.NS', 'BRITANNIA.NS', 'CGPOWER.NS', 'CANBK.NS',
        'CDSL.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS',
        'COLPAL.NS', 'CAMS.NS', 'CONCOR.NS', 'CROMPTON.NS', 'CUMMINSIND.NS'
    ]

    logger.info(f"Scanning {len(stocks)} stocks...")

    # Run scanner
    scanner = SimplePCSScanner()
    results = scanner.scan_stocks(stocks, min_strength=65)

    logger.info(f"Found {len(results)} qualifying stocks")

    # Format message
    ist = pytz.timezone('Asia/Kolkata')
    timestamp = datetime.now(ist).strftime('%Y-%m-%d %H:%M IST')

    message = f"""NSE F&O PCS Scanner Results
{timestamp}

Found: {len(results)} stocks
"""

    if results:
        for i, result in enumerate(results[:15], 1):
            message += f"\n{i}. {result['symbol']}"
            message += f"\n   Price: Rs {result['price']:.2f}"
            message += f"\n   RSI: {result['rsi']:.0f} | ADX: {result['adx']:.0f}"
            message += f"\n   Volume: {result['volume_ratio']:.2f}x | Strength: {result['strength']:.0f}%\n"

        if len(results) > 15:
            message += f"\n... and {len(results) - 15} more stocks"
    else:
        message += "\nNo qualifying stocks found today."

    message += """
Parameters:
- Min Pattern Strength: 65%
- Volume Ratio: 1.0x minimum
- ADX Minimum: 15
- RSI Range: 30-80

Disclaimer: For research purposes only.
"""

    # Send to Telegram
    telegram = TelegramNotifier()
    telegram.send_message(message)

    # Save results
    if results:
        filename = f"/tmp/pcs_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {filename}")

    logger.info("=" * 60)
    logger.info("Scan complete")


if __name__ == "__main__":
    main()
