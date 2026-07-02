#!/usr/bin/env python3
"""
NSE F&O PCS Scanner with Telegram Integration
Simplified scanner that identifies stocks meeting filter criteria
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import requests
from typing import List, Dict, Tuple
import os
import json

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

class SimplifiedPCSScanner:
    """Simplified PCS Scanner without TA library dependency"""

    def __init__(self):
        self.ist = pytz.timezone('Asia/Kolkata')
        self.stocks = {
            'Tier1': ['NIFTY.NS', 'BANKNIFTY.NS', 'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS',
                     'INFY.NS', 'ICICIBANK.NS', 'SBIN.NS', 'LT.NS', 'ITC.NS'],
            'Tier2': ['KOTAKBANK.NS', 'AXISBANK.NS', 'HCLTECH.NS', 'WIPRO.NS', 'MARUTI.NS',
                     'ASIANPAINT.NS', 'BHARTIARTL.NS', 'SUNPHARMA.NS'],
            'Tier3': ['BAJFINANCE.NS', 'BAJAJFINSV.NS', 'INDUSINDBK.NS', 'TECHM.NS', 'TITAN.NS',
                     'NESTLEIND.NS', 'ULTRACEMCO.NS', 'POWERGRID.NS', 'NTPC.NS', 'ONGC.NS',
                     'COALINDIA.NS', 'JSWSTEEL.NS', 'TATASTEEL.NS', 'HINDALCO.NS']
        }

    def get_stock_data(self, symbol: str, period: str = "3mo") -> pd.DataFrame:
        """Fetch stock data with error handling"""
        try:
            data = yf.download(symbol, period=period, progress=False, threads=False)
            if data is None or len(data) < 20:
                return None
            return data
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            return None

    def calculate_simple_metrics(self, data: pd.DataFrame, symbol: str) -> Dict:
        """Calculate simple metrics without TA library"""
        try:
            if data is None or len(data) < 20:
                return None

            close = data['Close']
            volume = data['Volume']
            high = data['High']
            low = data['Low']

            # Current values
            current_price = close.iloc[-1]
            prev_close = close.iloc[-2]

            # Price changes
            change_1d = ((current_price - prev_close) / prev_close) * 100
            change_5d = ((current_price - close.iloc[-5]) / close.iloc[-5]) * 100 if len(close) >= 5 else 0
            change_1m = ((current_price - close.iloc[-20]) / close.iloc[-20]) * 100 if len(close) >= 20 else 0

            # Volume metrics
            avg_volume = volume.tail(20).mean()
            current_volume = volume.iloc[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0

            # Support/Resistance (simple)
            sma_20 = close.tail(20).mean()
            sma_50 = close.tail(50).mean() if len(close) >= 50 else close.mean()

            # Distance from support
            distance_from_sma20 = ((current_price - sma_20) / sma_20) * 100

            # Volatility (simple)
            returns = close.pct_change().tail(20)
            volatility = returns.std() * np.sqrt(252) * 100  # Annualized %

            # RSI-like momentum (simplified)
            up_days = len(close.diff()[close.diff() > 0].tail(20))
            down_days = len(close.diff()[close.diff() < 0].tail(20))
            momentum_score = (up_days / (up_days + down_days + 1)) * 100 if (up_days + down_days) > 0 else 50

            # Volume trend
            volume_trend = "Increasing" if current_volume > avg_volume else "Decreasing"

            return {
                'symbol': symbol,
                'current_price': current_price,
                'change_1d': change_1d,
                'change_5d': change_5d,
                'change_1m': change_1m,
                'current_volume': current_volume,
                'avg_volume': avg_volume,
                'volume_ratio': volume_ratio,
                'volume_trend': volume_trend,
                'sma_20': sma_20,
                'sma_50': sma_50,
                'distance_from_sma20': distance_from_sma20,
                'momentum_score': momentum_score,
                'volatility': volatility,
                'price_above_sma20': current_price > sma_20,
                'price_above_sma50': current_price > sma_50
            }
        except Exception as e:
            print(f"Error calculating metrics for {symbol}: {e}")
            return None

    def apply_filters(self, metrics: Dict, filters: Dict) -> Tuple[bool, Dict]:
        """Apply PCS filter criteria"""
        if metrics is None:
            return False, {}

        filters = {
            'min_volume_ratio': filters.get('min_volume_ratio', 1.0),
            'min_momentum': filters.get('min_momentum', 45),
            'max_volatility': filters.get('max_volatility', 50),
            'price_above_sma20': filters.get('price_above_sma20', False),
            'min_change_1d': filters.get('min_change_1d', 0),
            'max_change_1d': filters.get('max_change_1d', 5)
        }

        signals = []
        score = 0

        # Volume check
        if metrics['volume_ratio'] >= filters['min_volume_ratio']:
            signals.append(f"✓ Volume Ratio: {metrics['volume_ratio']:.2f}x")
            score += 15
        else:
            signals.append(f"✗ Volume Ratio: {metrics['volume_ratio']:.2f}x (need {filters['min_volume_ratio']}x)")
            return False, {'signals': signals, 'score': score}

        # Momentum check
        if metrics['momentum_score'] >= filters['min_momentum']:
            signals.append(f"✓ Momentum Score: {metrics['momentum_score']:.1f}")
            score += 20

        # Volatility check
        if metrics['volatility'] <= filters['max_volatility']:
            signals.append(f"✓ Volatility: {metrics['volatility']:.1f}% (optimal range)")
            score += 15
        else:
            signals.append(f"⚠ Volatility: {metrics['volatility']:.1f}% (high)")

        # Price position
        if filters['price_above_sma20'] and metrics['price_above_sma20']:
            signals.append("✓ Price above SMA-20")
            score += 20
        elif not filters['price_above_sma20']:
            score += 10

        # Price change
        if filters['min_change_1d'] <= metrics['change_1d'] <= filters['max_change_1d']:
            signals.append(f"✓ 1D Change: {metrics['change_1d']:+.2f}%")
            score += 15

        # Volume trend
        if metrics['volume_trend'] == "Increasing":
            signals.append("✓ Volume Increasing")
            score += 10

        return score >= 50, {'signals': signals, 'score': min(score, 100)}

    def scan_stocks(self, tiers: List[str] = None, filters: Dict = None) -> List[Dict]:
        """Scan stocks and return those meeting criteria"""
        if tiers is None:
            tiers = ['Tier1', 'Tier2']
        if filters is None:
            filters = {
                'min_volume_ratio': 1.0,
                'min_momentum': 45,
                'max_volatility': 40,
                'price_above_sma20': True,
                'min_change_1d': 0,
                'max_change_1d': 5
            }

        results = []
        stocks_to_scan = []
        for tier in tiers:
            stocks_to_scan.extend(self.stocks.get(tier, []))

        print(f"\n🔍 Scanning {len(stocks_to_scan)} stocks...")

        for i, symbol in enumerate(stocks_to_scan, 1):
            print(f"  [{i}/{len(stocks_to_scan)}] {symbol.replace('.NS', '')}", end='', flush=True)

            # Get data
            data = self.get_stock_data(symbol)
            if data is None:
                print(" ✗ No data")
                continue

            # Calculate metrics
            metrics = self.calculate_simple_metrics(data, symbol)
            if metrics is None:
                print(" ✗ Calculation failed")
                continue

            # Apply filters
            meets_criteria, filter_details = self.apply_filters(metrics, filters)

            if meets_criteria:
                result = {**metrics, **filter_details}
                results.append(result)
                print(f" ✓ PASS (Score: {result['score']})")
            else:
                print(f" ✗ {filter_details.get('score', 0)}")

        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)
        return results

    def format_for_telegram(self, results: List[Dict]) -> str:
        """Format results for Telegram message"""
        if not results:
            return "❌ No stocks meeting filter criteria found."

        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist).strftime('%H:%M IST')

        message = f"📈 *NSE F&O PCS Scanner Results*\n_Updated: {now}_\n\n"
        message += f"🎯 *{len(results)} Stocks Meet Criteria*\n"
        message += "=" * 50 + "\n\n"

        for i, stock in enumerate(results[:15], 1):  # Telegram message limit
            symbol = stock['symbol'].replace('.NS', '')
            score = stock['score']
            change = stock['change_1d']
            momentum = stock['momentum_score']
            volume_ratio = stock['volume_ratio']

            emoji = "🟢" if score >= 75 else "🟡" if score >= 60 else "🔴"

            message += f"{i}. {emoji} *{symbol}*\n"
            message += f"   Score: {score}/100 | 1D: {change:+.2f}% | Vol: {volume_ratio:.2f}x\n"
            message += f"   Momentum: {momentum:.0f} | Price: ₹{stock['current_price']:.2f}\n"

            # Add signals
            for signal in stock['signals'][:3]:
                message += f"   • {signal}\n"
            message += "\n"

        message += "\n_Use the live dashboard for detailed analysis_"
        return message


def send_to_telegram(message: str, bot_token: str = None, chat_id: str = None) -> bool:
    """Send message to Telegram"""
    bot_token = bot_token or TELEGRAM_BOT_TOKEN
    chat_id = chat_id or TELEGRAM_CHAT_ID

    if not bot_token or not chat_id:
        print("❌ Telegram credentials not configured")
        print("   Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
        return False

    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Telegram Error: {e}")
        return False


def main():
    """Main function"""
    print("🚀 NSE F&O PCS Scanner with Telegram Integration\n")

    # Initialize scanner
    scanner = SimplifiedPCSScanner()

    # Scan with filters
    print("⚙️  Applying filters...")
    filters = {
        'min_volume_ratio': 0.8,      # At least 80% of average volume
        'min_momentum': 40,             # Momentum score >= 40
        'max_volatility': 50,           # Volatility <= 50% annualized
        'price_above_sma20': True,      # Price must be above 20-day MA
        'min_change_1d': -3,            # Not down more than 3%
        'max_change_1d': 5              # Not up more than 5%
    }

    results = scanner.scan_stocks(tiers=['Tier1', 'Tier2'], filters=filters)

    if results:
        print(f"\n✅ Found {len(results)} stocks meeting criteria!\n")

        # Format and display
        message = scanner.format_for_telegram(results)
        print(message)

        # Send to Telegram
        print("\n📱 Sending to Telegram...")
        if send_to_telegram(message):
            print("✅ Message sent successfully!")
        else:
            print("⚠️  Could not send to Telegram - see credentials above")

        # Save results to JSON
        with open('/tmp/pcs_scan_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print("\n💾 Results saved to /tmp/pcs_scan_results.json")
    else:
        print("\n❌ No stocks meeting filter criteria")
        message = scanner.format_for_telegram([])
        print(message)


if __name__ == "__main__":
    main()
