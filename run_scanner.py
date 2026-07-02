#!/usr/bin/env python3
"""
NSE F&O PCS Scanner - Run Locally
Complete solution for scanning stocks and sending to Telegram
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import requests
from typing import List, Dict, Tuple
import os
import sys
from pathlib import Path

# ============================================================================
# CONFIGURATION - EDIT THIS
# ============================================================================

# Get Telegram credentials from environment or edit here
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', 'YOUR_CHAT_ID_HERE')

# Filter Configuration
SCAN_CONFIG = {
    'min_volume_ratio': 0.8,      # 80% of average volume
    'min_momentum': 40,             # Momentum score >= 40
    'max_volatility': 50,           # Volatility <= 50%
    'price_above_sma20': True,      # Must be above 20-day MA
    'min_change_1d': -3,            # Not down more than 3%
    'max_change_1d': 5              # Not up more than 5%
}

# Stocks to scan (organized by liquidity tier)
STOCKS_TO_SCAN = {
    'Tier1': [
        'NIFTY.NS', 'BANKNIFTY.NS',
        'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS',
        'ICICIBANK.NS', 'SBIN.NS', 'LT.NS', 'ITC.NS'
    ],
    'Tier2': [
        'KOTAKBANK.NS', 'AXISBANK.NS', 'HCLTECH.NS', 'WIPRO.NS',
        'MARUTI.NS', 'ASIANPAINT.NS', 'BHARTIARTL.NS', 'SUNPHARMA.NS'
    ],
    'Tier3': [
        'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'INDUSINDBK.NS', 'TECHM.NS',
        'TITAN.NS', 'NESTLEIND.NS', 'ULTRACEMCO.NS', 'POWERGRID.NS',
        'NTPC.NS', 'ONGC.NS', 'COALINDIA.NS', 'JSWSTEEL.NS',
        'TATASTEEL.NS', 'HINDALCO.NS'
    ]
}

# ============================================================================
# SCANNER CLASS
# ============================================================================

class PCSScanner:
    """PCS Scanner with Telegram Integration"""

    def __init__(self):
        self.ist = pytz.timezone('Asia/Kolkata')

    def get_stock_data(self, symbol: str, period: str = "3mo") -> pd.DataFrame:
        """Fetch stock data"""
        try:
            print(f"  Fetching {symbol}...", end='', flush=True)
            data = yf.download(symbol, period=period, progress=False, threads=False)
            if data is None or len(data) < 20:
                print(" ✗ No data")
                return None
            print(f" ✓ ({len(data)} candles)")
            return data
        except Exception as e:
            print(f" ✗ Error: {e}")
            return None

    def calculate_metrics(self, data: pd.DataFrame, symbol: str) -> Dict:
        """Calculate PCS metrics"""
        try:
            close = data['Close']
            volume = data['Volume']
            high = data['High']
            low = data['Low']

            # Price metrics
            current_price = close.iloc[-1]
            prev_close = close.iloc[-2]
            change_1d = ((current_price - prev_close) / prev_close) * 100
            change_5d = ((current_price - close.iloc[-5]) / close.iloc[-5]) * 100
            change_1m = ((current_price - close.iloc[-20]) / close.iloc[-20]) * 100

            # Volume metrics
            avg_volume = volume.tail(20).mean()
            current_volume = volume.iloc[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0

            # Support/Resistance
            sma_20 = close.tail(20).mean()
            sma_50 = close.tail(50).mean() if len(close) >= 50 else close.mean()
            distance_from_sma20 = ((current_price - sma_20) / sma_20) * 100

            # Volatility
            returns = close.pct_change().tail(20)
            volatility = returns.std() * np.sqrt(252) * 100

            # Momentum (simplified RSI concept)
            up_days = len(close.diff()[close.diff() > 0].tail(20))
            down_days = len(close.diff()[close.diff() < 0].tail(20))
            momentum_score = (up_days / (up_days + down_days + 1)) * 100 if (up_days + down_days) > 0 else 50

            return {
                'symbol': symbol,
                'current_price': current_price,
                'change_1d': change_1d,
                'change_5d': change_5d,
                'change_1m': change_1m,
                'current_volume': current_volume,
                'avg_volume': avg_volume,
                'volume_ratio': volume_ratio,
                'sma_20': sma_20,
                'sma_50': sma_50,
                'distance_from_sma20': distance_from_sma20,
                'momentum_score': momentum_score,
                'volatility': volatility,
                'price_above_sma20': current_price > sma_20,
                'price_above_sma50': current_price > sma_50
            }
        except Exception as e:
            print(f"  Calculation error: {e}")
            return None

    def apply_filters(self, metrics: Dict, filters: Dict) -> Tuple[bool, Dict]:
        """Apply filter criteria and calculate score"""
        if metrics is None:
            return False, {}

        signals = []
        score = 0

        # Volume check (mandatory)
        if metrics['volume_ratio'] >= filters['min_volume_ratio']:
            signals.append(f"✓ Volume: {metrics['volume_ratio']:.2f}x")
            score += 20
        else:
            return False, {'signals': signals, 'score': score}

        # Momentum check
        if metrics['momentum_score'] >= filters['min_momentum']:
            signals.append(f"✓ Momentum: {metrics['momentum_score']:.0f}")
            score += 25

        # Volatility check
        if metrics['volatility'] <= filters['max_volatility']:
            signals.append(f"✓ Vol: {metrics['volatility']:.1f}%")
            score += 15

        # Price position
        if filters['price_above_sma20'] and metrics['price_above_sma20']:
            signals.append("✓ Price>SMA20")
            score += 25

        # Price change
        if filters['min_change_1d'] <= metrics['change_1d'] <= filters['max_change_1d']:
            signals.append(f"✓ 1D: {metrics['change_1d']:+.2f}%")
            score += 15

        return score >= 50, {'signals': signals, 'score': min(score, 100)}

    def scan(self, tiers: List[str], filters: Dict) -> List[Dict]:
        """Scan stocks and return qualified ones"""
        results = []
        stocks = []
        for tier in tiers:
            stocks.extend(STOCKS_TO_SCAN.get(tier, []))

        print(f"\n📊 Scanning {len(stocks)} stocks\n")

        for i, symbol in enumerate(stocks, 1):
            data = self.get_stock_data(symbol)
            if data is None:
                continue

            metrics = self.calculate_metrics(data, symbol)
            if metrics is None:
                continue

            meets_criteria, filter_info = self.apply_filters(metrics, filters)

            if meets_criteria:
                result = {**metrics, **filter_info}
                results.append(result)
                print(f"  ✅ QUALIFIED - Score: {result['score']}/100")

        results.sort(key=lambda x: x['score'], reverse=True)
        return results


# ============================================================================
# TELEGRAM INTEGRATION
# ============================================================================

def send_to_telegram(message: str) -> bool:
    """Send formatted message to Telegram"""
    if TELEGRAM_BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE' or TELEGRAM_CHAT_ID == 'YOUR_CHAT_ID_HERE':
        print("\n⚠️  Telegram credentials not configured")
        print("   Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
        print("   Or edit the script to add your credentials")
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'Markdown'
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Telegram error: {e}")
        return False


def format_message(results: List[Dict]) -> str:
    """Format results for Telegram"""
    if not results:
        return "❌ No stocks meeting criteria"

    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist).strftime('%d %b %H:%M IST')

    msg = f"📈 *PCS Scan Results* - {now}\n"
    msg += f"🎯 *{len(results)} Qualified Stocks*\n"
    msg += "=" * 40 + "\n\n"

    for i, stock in enumerate(results[:15], 1):  # Telegram limit
        symbol = stock['symbol'].replace('.NS', '')
        score = stock['score']
        change = stock['change_1d']
        momentum = stock['momentum_score']
        vol_ratio = stock['volume_ratio']

        emoji = "🟢" if score >= 75 else "🟡" if score >= 60 else "🔴"
        msg += f"{i}. {emoji} *{symbol}*\n"
        msg += f"   Score: {score} | 1D: {change:+.1f}% | Vol: {vol_ratio:.2f}x\n"
        msg += f"   Price: ₹{stock['current_price']:.2f} | Momentum: {momentum:.0f}\n"

        for sig in stock['signals'][:2]:
            msg += f"   • {sig}\n"
        msg += "\n"

    return msg


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("\n" + "=" * 60)
    print(" NSE F&O PCS SCANNER WITH TELEGRAM")
    print("=" * 60 + "\n")

    print("⚙️  Configuration:")
    print(f"   Min Volume Ratio: {SCAN_CONFIG['min_volume_ratio']}x")
    print(f"   Min Momentum: {SCAN_CONFIG['min_momentum']}")
    print(f"   Max Volatility: {SCAN_CONFIG['max_volatility']}%")
    print(f"   Price > SMA20: {SCAN_CONFIG['price_above_sma20']}")

    # Initialize scanner
    scanner = PCSScanner()

    # Run scan
    print("\n🔍 Starting scan on Tier1 & Tier2 stocks...")
    results = scanner.scan(['Tier1', 'Tier2'], SCAN_CONFIG)

    if results:
        print(f"\n✅ Found {len(results)} stocks!\n")

        # Format and display
        message = format_message(results)
        print(message)

        # Send to Telegram
        print("📱 Sending to Telegram...")
        if send_to_telegram(message):
            print("✅ Sent successfully!\n")
        else:
            print("⚠️  Could not send (see above)\n")

        # Save results
        csv_path = f"pcs_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df = pd.DataFrame(results)
        df.to_csv(csv_path, index=False)
        print(f"💾 Saved: {csv_path}\n")
    else:
        print("\n❌ No stocks qualified\n")

    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
