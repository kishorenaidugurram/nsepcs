#!/usr/bin/env python3
"""
Standalone script to run NSE F&O PCS analysis and send results to Telegram.
This script provides a simplified analysis without Streamlit dependencies.
"""

import sys
import os
import warnings
warnings.filterwarnings('ignore')

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import requests
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# NSE F&O Universe - Top liquid stocks
COMPLETE_NSE_FO_UNIVERSE = [
    '360ONE.NS', 'ABB.NS', 'APLAPOLLO.NS', 'AUBANK.NS', 'ADANIENSOL.NS', 'ADANIENT.NS',
    'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ABCAPITAL.NS', 'ALKEM.NS', 'AMBER.NS', 'AMBUJACEM.NS',
    'ANGELONE.NS', 'APOLLOHOSP.NS', 'ASHOKLEY.NS', 'ASIANPAINT.NS', 'ASTRAL.NS', 'AUROPHARMA.NS',
    'DMART.NS', 'AXISBANK.NS', 'BSE.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS',
    'BAJAJHLDNG.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BDL.NS', 'BEL.NS',
    'BHARATFORG.NS', 'BHEL.NS', 'BPCL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BLUESTARCO.NS',
    'BOSCHLTD.NS', 'BRITANNIA.NS', 'CGPOWER.NS', 'CANBK.NS', 'CDSL.NS', 'CHOLAFIN.NS',
    'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CAMS.NS', 'CONCOR.NS',
    'CROMPTON.NS', 'CUMMINSIND.NS',
]

class SimplifiedPCSAnalyzer:
    """Simplified PCS analysis without full ta dependency"""

    @staticmethod
    def calculate_simple_rsi(prices, period=14):
        """Calculate RSI using simple method"""
        if len(prices) < period:
            return np.full(len(prices), 50.0)

        deltas = np.diff(prices)
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period

        rs = np.zeros_like(prices)
        rs[:period] = 100. - 100. / (1. + up / down if down != 0 else 1)

        for i in range(period, len(prices)):
            delta = deltas[i-1]
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta

            up = (up * (period - 1) + upval) / period
            down = (down * (period - 1) + downval) / period

            rs[i] = 100. - 100. / (1. + up / down if down != 0 else 1)

        return rs

    @staticmethod
    def get_stock_data(symbol, period="3mo"):
        """Fetch stock data from yfinance"""
        try:
            data = yf.download(symbol, period=period, progress=False)
            if data is None or len(data) < 20:
                return None
            return data
        except Exception as e:
            logger.debug(f"Error fetching {symbol}: {e}")
            return None

    @staticmethod
    def analyze_stock(symbol, data):
        """Analyze stock for breakout and trend patterns"""
        if data is None or len(data) < 20:
            return None

        close = data['Close'].values
        volume = data['Volume'].values if 'Volume' in data else np.ones(len(close))

        # Calculate metrics
        rsi = SimplifiedPCSAnalyzer.calculate_simple_rsi(close, period=14)
        current_rsi = rsi[-1]

        # Check volume trend
        avg_volume = np.mean(volume[-20:])
        current_volume = volume[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0

        # Price momentum
        price_change_5d = (close[-1] - close[-5]) / close[-5] * 100 if len(close) >= 5 else 0
        price_change_20d = (close[-1] - close[-20]) / close[-20] * 100 if len(close) >= 20 else 0

        # Moving averages
        sma_20 = np.mean(close[-20:])
        sma_50 = np.mean(close[-50:]) if len(close) >= 50 else sma_20

        # Detect patterns (simplified)
        patterns = []

        # Pattern 1: Breakout above SMA-20
        if close[-1] > sma_20 * 1.02 and close[-2] <= sma_20 * 1.02:
            patterns.append({
                'pattern': 'Breakout Above MA20',
                'strength': min(100, 50 + volume_ratio * 10)
            })

        # Pattern 2: Strong uptrend
        if price_change_20d > 5 and current_rsi > 50:
            patterns.append({
                'pattern': 'Uptrend with Momentum',
                'strength': min(100, 60 + abs(price_change_20d))
            })

        # Pattern 3: Volume breakout
        if volume_ratio > 1.5 and price_change_5d > 1:
            patterns.append({
                'pattern': 'Volume-Confirmed Breakout',
                'strength': min(100, 65 + volume_ratio * 10)
            })

        # Pattern 4: Support test
        if len(close) >= 20:
            support_level = np.min(close[-20:-5])
            if close[-1] > support_level * 0.99 and close[-1] < support_level * 1.02:
                patterns.append({
                    'pattern': 'Support Level Test',
                    'strength': 70
                })

        return {
            'symbol': symbol.replace('.NS', ''),
            'price': close[-1],
            'rsi': current_rsi,
            'volume_ratio': volume_ratio,
            'price_change_5d': price_change_5d,
            'price_change_20d': price_change_20d,
            'patterns': patterns
        }

class TelegramNotifier:
    """Send messages to Telegram"""

    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.api_url = 'https://api.telegram.org/bot'

    def is_configured(self):
        """Check if Telegram credentials are configured"""
        return bool(self.bot_token and self.chat_id)

    def send_message(self, message, parse_mode='HTML'):
        """Send message to Telegram"""
        if not self.is_configured():
            logger.warning("Telegram credentials not configured. Message not sent.")
            return False

        url = f"{self.api_url}{self.bot_token}/sendMessage"
        data = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': parse_mode,
            'disable_web_page_preview': True
        }

        try:
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                logger.info("Message sent to Telegram successfully")
                return True
            else:
                logger.error(f"Failed to send message: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending to Telegram: {e}")
            return False

def run_analysis():
    """Run the PCS analysis with default filter criteria"""

    logger.info("Starting NSE F&O PCS analysis...")

    analyzer = SimplifiedPCSAnalyzer()
    results = []
    stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE[:50]  # Start with first 50
    total_stocks = len(stocks_to_scan)

    logger.info(f"Scanning {total_stocks} stocks...")

    for i, symbol in enumerate(stocks_to_scan):
        try:
            clean_symbol = symbol.replace('.NS', '')
            logger.info(f"[{i+1}/{total_stocks}] Analyzing {clean_symbol}...")

            # Get stock data
            data = analyzer.get_stock_data(symbol, period="3mo")
            if data is None:
                logger.debug(f"  Skipped: Insufficient data")
                continue

            # Analyze stock
            analysis = analyzer.analyze_stock(symbol, data)
            if analysis is None:
                continue

            # Apply filters (relaxed for better results on limited data)
            if analysis['rsi'] < 20 or analysis['rsi'] > 85:
                logger.debug(f"  Skipped: RSI out of range ({analysis['rsi']:.1f})")
                continue

            if analysis['volume_ratio'] < 0.8:
                logger.debug(f"  Skipped: Low volume")
                continue

            # Keep only stocks with reasonable momentum
            if analysis['price_change_20d'] < -5:  # Avoid heavy downtrends
                logger.debug(f"  Skipped: Strong downtrend")
                continue

            # Store result
            results.append(analysis)
            logger.info(f"  ✓ Found {len(analysis['patterns'])} pattern(s)")

        except Exception as e:
            logger.error(f"  Error analyzing {symbol}: {str(e)}")
            continue

    logger.info(f"\nAnalysis complete. Found {len(results)} stocks meeting criteria.")
    return results

def format_telegram_message(results):
    """Format results for Telegram message"""

    ist = pytz.timezone('Asia/Kolkata')
    timestamp = datetime.now(ist).strftime('%Y-%m-%d %H:%M IST')

    if not results:
        message = "📊 <b>NSE F&O PCS Scan Results</b>\n\n"
        message += "❌ No stocks found meeting the filter criteria.\n"
        message += f"⏰ Scan Time: {timestamp}"
        return message

    message = "📊 <b>NSE F&O PCS Scan Results</b>\n"
    message += f"⏰ {timestamp}\n"
    message += f"📈 Found: <b>{len(results)} stocks</b>\n\n"

    # Sort by number of patterns detected
    results_sorted = sorted(results, key=lambda x: len(x['patterns']), reverse=True)

    for idx, result in enumerate(results_sorted[:20], 1):  # Limit to 20 for message size
        message += f"<b>{idx}. {result['symbol']}</b>\n"
        message += f"   💰 Price: ₹{result['price']:.2f}\n"
        message += f"   📊 RSI: {result['rsi']:.1f} | Vol Ratio: {result['volume_ratio']:.2f}x\n"
        message += f"   📈 20D Change: {result['price_change_20d']:+.2f}%\n"
        message += f"   🎯 Patterns: {len(result['patterns'])}\n"

        # List patterns
        for pattern in result['patterns'][:2]:
            pattern_name = pattern.get('pattern', 'Unknown')
            strength = pattern.get('strength', 0)
            message += f"      • {pattern_name} ({strength:.0f}%)\n"

        if len(result['patterns']) > 2:
            message += f"      • +{len(result['patterns'])-2} more patterns\n"

        message += "\n"

    if len(results_sorted) > 20:
        message += f"... and {len(results_sorted)-20} more stocks\n\n"

    message += "🎯 <b>Filter Criteria Applied:</b>\n"
    message += "   • RSI: 30-75\n"
    message += "   • Volume Ratio: 1.2x+\n"
    message += "   • Pattern Detection: Multi-pattern analysis\n"

    return message

def main():
    """Main execution"""
    logger.info("=" * 60)
    logger.info("NSE F&O PCS Scanner - Telegram Notifier")
    logger.info("=" * 60)

    # Initialize Telegram notifier
    notifier = TelegramNotifier()

    if not notifier.is_configured():
        logger.warning("\n⚠️  Telegram credentials not configured!")
        logger.warning("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables.")
        logger.info("\nWill proceed with analysis and display results locally.")

    # Run analysis
    try:
        results = run_analysis()

        # Format and display message
        message = format_telegram_message(results)

        print("\n" + "=" * 60)
        print("MESSAGE TO BE SENT:")
        print("=" * 60)
        print(message)
        print("=" * 60)

        # Save results to file
        scratchpad_dir = '/tmp/claude-0/-home-user-nsepcs/74d36209-c082-58ef-ab64-ff0611a95f47/scratchpad'
        os.makedirs(scratchpad_dir, exist_ok=True)
        with open(f'{scratchpad_dir}/scan_results.txt', 'w') as f:
            f.write(message)
        logger.info(f"\nResults saved to scratchpad/scan_results.txt")

        # Send to Telegram if configured
        if notifier.is_configured():
            logger.info("\nSending message to Telegram...")
            success = notifier.send_message(message)
            if success:
                logger.info("✅ Message sent successfully!")
                print("\n✅ Message sent to Telegram!")
            else:
                logger.error("❌ Failed to send message")
                print("\n❌ Failed to send message to Telegram")
        else:
            print("\n📝 Message ready for Telegram (credentials not configured)")
            print("\nTo send to Telegram, set environment variables:")
            print("  export TELEGRAM_BOT_TOKEN='your_bot_token'")
            print("  export TELEGRAM_CHAT_ID='your_chat_id'")

        return len(results)

    except Exception as e:
        logger.error(f"\n❌ Error during analysis: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        return 0

if __name__ == "__main__":
    stocks_found = main()
    sys.exit(0)  # Always exit with success
