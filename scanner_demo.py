#!/usr/bin/env python3
"""
NSE F&O PCS Scanner - Demo Version (without Telegram)
Runs the PCS scanner and displays filtered results
"""

import os
import sys
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import pytz
import warnings

warnings.filterwarnings('ignore')

# Filter configuration
MIN_PCS_SCORE = float(os.getenv('MIN_PCS_SCORE', '55'))
MIN_VOLUME_RATIO = float(os.getenv('MIN_VOLUME_RATIO', '1.0'))
MAX_STOCKS = int(os.getenv('MAX_STOCKS', '40'))

# Stock list (popular NSE F&O stocks)
DEMO_STOCKS = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
    'SBIN.NS', 'LT.NS', 'ITC.NS', 'KOTAKBANK.NS', 'AXISBANK.NS',
    'MARUTI.NS', 'ASIANPAINT.NS', 'BHARTIARTL.NS', 'SUNPHARMA.NS',
    'TATAMOTORS.NS', 'ADANIENT.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS',
    'INDUSINDBK.NS', 'TECHM.NS'
]


# Simple technical indicators implementation
def calculate_rsi(prices, period=14):
    """Calculate RSI (Relative Strength Index)"""
    deltas = np.diff(prices)
    if len(deltas) < period:
        return np.zeros(len(prices))

    seed = deltas[:period+1]
    up = seed[seed>=0].sum()/period if period > 0 else 0
    down = -seed[seed<0].sum()/period if period > 0 else 0
    rs = up/down if down != 0 else 0
    rsi = np.zeros(len(prices))
    rsi[:period] = 100. - 100./(1.+rs) if (1.+rs) != 0 else 50

    for i in range(period, len(prices)):
        delta = deltas[i-1]
        if delta>0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta

        up = (up*(period-1) + upval)/period
        down = (down*(period-1) + downval)/period
        rs = up/down if down != 0 else 0
        rsi[i] = 100. - 100./(1.+rs) if (1.+rs) != 0 else 50

    return rsi


def calculate_sma(prices, period=20):
    """Calculate Simple Moving Average"""
    return pd.Series(prices).rolling(window=period).mean().values


def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD"""
    series = pd.Series(prices)
    ema_fast = series.ewm(span=fast).mean()
    ema_slow = series.ewm(span=slow).mean()
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=signal).mean()
    return macd.values, macd_signal.values, (macd - macd_signal).values


def calculate_bollinger_bands(prices, period=20, num_std=2):
    """Calculate Bollinger Bands"""
    series = pd.Series(prices)
    sma = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    upper = sma + (std * num_std)
    lower = sma - (std * num_std)
    return upper.values, sma.values, lower.values


def calculate_adx_simple(high, low, close, period=14):
    """Calculate simplified ADX"""
    try:
        high_s = pd.Series(high)
        low_s = pd.Series(low)
        close_s = pd.Series(close)

        tr1 = high_s - low_s
        tr2 = abs(high_s - close_s.shift(1))
        tr3 = abs(low_s - close_s.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()

        plus_dm = high_s.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm = low_s.shift(1) - low_s
        minus_dm[minus_dm < 0] = 0

        plus_di = 100 * plus_dm.rolling(period).mean() / (atr + 1e-6)
        minus_di = 100 * minus_dm.rolling(period).mean() / (atr + 1e-6)

        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-6)
        adx = dx.rolling(period).mean()

        return adx.values
    except:
        return np.full(len(close), 20)  # Return neutral value on error


class PCSScanner:
    """Simplified PCS Scanner for filtering stocks"""

    def __init__(self):
        self.ist = pytz.timezone('Asia/Kolkata')

    def get_stock_data(self, symbol, period="3mo"):
        """Fetch and process stock data"""
        try:
            data = yf.download(symbol, period=period, progress=False, quiet=True)

            if data is None or len(data) < 20:
                return None

            # Calculate technical indicators using simple implementations
            data['RSI'] = calculate_rsi(data['Close'].values)
            data['SMA_20'] = calculate_sma(data['Close'].values, 20)
            data['SMA_50'] = calculate_sma(data['Close'].values, 50)
            bb_upper, bb_mid, bb_lower = calculate_bollinger_bands(data['Close'].values, 20)
            data['BB_upper'] = bb_upper
            data['BB_lower'] = bb_lower
            macd, macd_signal, macd_hist = calculate_macd(data['Close'].values)
            data['MACD'] = macd
            data['MACD_signal'] = macd_signal
            data['MACD_hist'] = macd_hist
            data['ADX'] = calculate_adx_simple(
                data['High'].values,
                data['Low'].values,
                data['Close'].values
            )

            return data
        except Exception as e:
            return None

    def calculate_pcs_score(self, data, symbol):
        """Calculate PCS (Put Credit Spread) score"""
        try:
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]
            current_macd_hist = data['MACD_hist'].iloc[-1]
            sma_20 = data['SMA_20'].iloc[-1]
            bb_lower = data['BB_lower'].iloc[-1]

            score = 50  # Base score
            details = []

            # 1. RSI Analysis (30% weight)
            if pd.notna(current_rsi):
                if 45 <= current_rsi <= 65:
                    score += 15
                    details.append(f"RSI optimal ({current_rsi:.1f})")
                elif 40 <= current_rsi <= 70:
                    score += 10
                    details.append(f"RSI good ({current_rsi:.1f})")
                elif current_rsi < 30:
                    score += 5
                    details.append(f"RSI oversold ({current_rsi:.1f})")

            # 2. Trend Strength (25% weight)
            if pd.notna(current_adx) and current_adx > 0:
                if current_adx > 25:
                    score += 12
                    details.append(f"Strong trend (ADX: {current_adx:.1f})")
                elif current_adx > 20:
                    score += 8
                    details.append(f"Good trend (ADX: {current_adx:.1f})")

            # 3. Support Proximity (20% weight)
            if pd.notna(sma_20) and current_price > sma_20:
                score += 10
                if pd.notna(bb_lower) and bb_lower > 0:
                    distance_to_support = ((current_price - bb_lower) / current_price) * 100
                    details.append(f"Above SMA20, {distance_to_support:.1f}% from BB")
                else:
                    details.append("Above SMA20")

            # 4. MACD (15% weight)
            if pd.notna(current_macd_hist) and current_macd_hist > 0:
                score += 7
                details.append("MACD positive")

            # 5. Volume (10% weight)
            avg_volume = data['Volume'].tail(20).mean()
            current_volume = data['Volume'].iloc[-1]
            if current_volume > avg_volume:
                score += 5
                details.append("Vol above avg")

            return min(score, 100), details

        except Exception as e:
            return 50, ["Unable to calculate indicators"]

    def check_volume_criteria(self, data, min_ratio=1.0):
        """Check if volume meets criteria"""
        try:
            recent_volume = data['Volume'].tail(5).mean()
            historical_volume = data['Volume'].tail(50).mean()
            ratio = recent_volume / historical_volume if historical_volume > 0 else 0
            return ratio >= min_ratio, ratio
        except:
            return False, 0

    def scan_stocks(self, stocks, min_score=55, min_volume_ratio=1.0):
        """Scan stocks and return filtered results"""
        results = []

        for i, symbol in enumerate(stocks, 1):
            print(f"[{i}/{len(stocks)}] {symbol}...", end='\r')

            data = self.get_stock_data(symbol)
            if data is None:
                continue

            # Check volume criteria
            volume_ok, volume_ratio = self.check_volume_criteria(data, min_volume_ratio)
            if not volume_ok:
                continue

            # Calculate score
            score, details = self.calculate_pcs_score(data, symbol)

            # Filter by score
            if score >= min_score:
                current_price = data['Close'].iloc[-1]
                current_rsi = data['RSI'].iloc[-1]

                results.append({
                    'Symbol': symbol.replace('.NS', ''),
                    'Price': round(current_price, 2),
                    'PCS Score': int(score),
                    'RSI': round(current_rsi, 1) if pd.notna(current_rsi) else 0,
                    'Volume Ratio': round(volume_ratio, 2),
                    'Details': ' | '.join(details)
                })

        print(" " * 60, end='\r')  # Clear the progress line
        if results:
            return pd.DataFrame(results).sort_values('PCS Score', ascending=False)
        return pd.DataFrame()


def main():
    """Main function to run scanner"""

    print("=" * 80)
    print("🚀 NSE F&O PCS Scanner - Demo Mode")
    print("=" * 80)
    print(f"📊 Filter: PCS Score ≥ {MIN_PCS_SCORE}, Volume Ratio ≥ {MIN_VOLUME_RATIO}")
    print(f"📈 Scanning {min(len(DEMO_STOCKS), MAX_STOCKS)} stocks...\n")

    # Run scanner
    scanner = PCSScanner()
    results = scanner.scan_stocks(
        DEMO_STOCKS[:MAX_STOCKS],
        min_score=MIN_PCS_SCORE,
        min_volume_ratio=MIN_VOLUME_RATIO
    )

    if results.empty:
        print("\n❌ No stocks meeting filter criteria found.")
        print(f"Filter: PCS Score ≥ {MIN_PCS_SCORE}, Volume Ratio ≥ {MIN_VOLUME_RATIO}")
        print("\n💡 Try lowering MIN_PCS_SCORE or MIN_VOLUME_RATIO")
        return

    # Display results
    print("\n" + "=" * 80)
    print("RESULTS - Stocks Meeting Filter Criteria")
    print("=" * 80)

    # Create display dataframe
    display_df = results[['Symbol', 'Price', 'PCS Score', 'RSI', 'Volume Ratio']].copy()
    print(display_df.to_string(index=False))

    print("\n" + "=" * 80)
    print("DETAILED VIEW")
    print("=" * 80)
    for idx, row in results.iterrows():
        print(f"\n{idx+1}. {row['Symbol']}")
        print(f"   Price: ₹{row['Price']}")
        print(f"   PCS Score: {row['PCS Score']}/100")
        print(f"   RSI: {row['RSI']}")
        print(f"   Volume Ratio: {row['Volume Ratio']}")
        print(f"   Analysis: {row['Details']}")

    # Save results to file
    csv_path = f"pcs_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    results.to_csv(csv_path, index=False)
    print(f"\n💾 Results saved to {csv_path}")

    print("\n" + "=" * 80)
    print("📱 TO SEND RESULTS TO TELEGRAM:")
    print("=" * 80)
    print("1. Read the setup guide: TELEGRAM_SETUP.md")
    print("2. Create a Telegram bot with @BotFather")
    print("3. Set environment variables:")
    print("   export TELEGRAM_BOT_TOKEN='your_token'")
    print("   export TELEGRAM_CHAT_ID='your_chat_id'")
    print("4. Run: python scanner_telegram.py")
    print("=" * 80)


if __name__ == "__main__":
    main()
