#!/usr/bin/env python3
"""
Simplified NSE F&O Stock Scanner with Telegram Integration
Self-contained technical indicators, no external ta library required
"""

import os
import sys
import json
import warnings
from datetime import datetime
import pytz
from typing import List, Dict, Tuple
import requests
import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings('ignore')

# ============================================================================
# TECHNICAL INDICATORS (Self-contained implementations)
# ============================================================================

def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down if down != 0 else 0
    rsi = np.zeros_like(prices, dtype=float)
    rsi[:period] = 100. - 100. / (1. + rs)

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

        rs = up / down if down != 0 else 0
        rsi[i] = 100. - 100. / (1. + rs)

    return rsi

def calculate_adx(high, low, close, period=14):
    """Calculate ADX indicator"""
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()

    plus_dm = high - high.shift(1)
    minus_dm = low.shift(1) - low

    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0

    plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr)

    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(period).mean()

    return adx.fillna(0)

def calculate_sma(prices, period):
    """Calculate Simple Moving Average"""
    return pd.Series(prices).rolling(period).mean().values

def calculate_ema(prices, period):
    """Calculate Exponential Moving Average"""
    return pd.Series(prices).ewm(span=period).mean().values

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD"""
    ema_fast = pd.Series(prices).ewm(span=fast).mean()
    ema_slow = pd.Series(prices).ewm(span=slow).mean()
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=signal).mean()
    macd_hist = macd - macd_signal
    return macd.values, macd_signal.values, macd_hist.values

def calculate_bollinger_bands(prices, period=20, num_std=2):
    """Calculate Bollinger Bands"""
    sma = pd.Series(prices).rolling(period).mean()
    std = pd.Series(prices).rolling(period).std()
    upper = sma + (std * num_std)
    lower = sma - (std * num_std)
    return upper.values, sma.values, lower.values

# ============================================================================
# STOCK SCANNER CLASS
# ============================================================================

class SimpleStockScanner:
    """Simplified stock scanner without ta library"""

    def __init__(self):
        self.ist = pytz.timezone('Asia/Kolkata')

    def get_stock_data(self, symbol, period="3mo"):
        """Get stock data and calculate technical indicators"""
        try:
            stock = yf.Ticker(symbol)
            data = stock.history(period=period, interval="1d")

            if len(data) < 20:
                return None

            # Calculate indicators
            close = data['Close'].values
            high = data['High'].values
            low = data['Low'].values

            data['RSI'] = calculate_rsi(close)
            data['SMA_20'] = calculate_sma(close, 20)
            data['SMA_50'] = calculate_sma(close, 50)
            data['EMA_20'] = calculate_ema(close, 20)

            upper, middle, lower = calculate_bollinger_bands(close)
            data['BB_upper'] = upper
            data['BB_middle'] = middle
            data['BB_lower'] = lower

            data['MACD'], data['MACD_signal'], data['MACD_hist'] = calculate_macd(close)
            data['ADX'] = calculate_adx(data['High'], data['Low'], data['Close'])

            return data

        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            return None

    def check_volume_criteria(self, data, min_ratio=1.0):
        """Check if volume meets criteria"""
        if len(data) < 21:
            return False, 0, {}

        current_volume = data['Volume'].iloc[-1]
        avg_20_volume = data['Volume'].tail(21).iloc[:-1].mean()
        volume_ratio = current_volume / avg_20_volume if avg_20_volume > 0 else 0

        details = {
            'current_volume': current_volume,
            'avg_20_volume': avg_20_volume,
            'ratio_20d': volume_ratio
        }

        return volume_ratio >= min_ratio, volume_ratio, details

    def detect_patterns(self, data, symbol, filters):
        """Detect chart patterns"""
        if len(data) < 50:
            return []

        patterns = []

        # Get current metrics
        current_price = data['Close'].iloc[-1]
        current_rsi = data['RSI'].iloc[-1]
        current_adx = data['ADX'].iloc[-1]
        sma_20 = data['SMA_20'].iloc[-1]
        ema_20 = data['EMA_20'].iloc[-1]

        # Filter checks
        if not (filters['rsi_min'] <= current_rsi <= filters['rsi_max']):
            return []

        if current_adx < filters['adx_min']:
            return []

        # MA Support check
        if filters.get('ma_support', True):
            ma_type = filters.get('ma_type', 'SMA')
            ma_tolerance = filters.get('ma_tolerance', 3) / 100
            support_ma = sma_20 if ma_type == 'SMA' else ema_20

            if current_price < support_ma * (1 - ma_tolerance):
                return []

        # Current Day Breakout Detection
        if len(data) >= 21:
            current_day = data.iloc[-1]
            lookback_data = data.iloc[:-1].tail(20)

            resistance = lookback_data['High'].max()
            support = lookback_data['Low'].min()

            current_close = current_day['Close']
            current_high = current_day['High']
            current_volume = current_day['Volume']
            avg_volume = lookback_data['Volume'].mean()

            # Breakout condition
            if (current_close > resistance * 1.005 and
                current_volume > avg_volume * filters.get('min_volume_ratio', 1.2)):

                consolidation = ((resistance - support) / support) * 100
                if consolidation < 15:
                    breakout_pct = ((current_close - resistance) / resistance) * 100
                    volume_ratio = current_volume / avg_volume

                    strength = min(100, 60 + (breakout_pct * 3) + (volume_ratio * 5))

                    patterns.append({
                        'type': 'Current Day Breakout',
                        'strength': strength,
                        'confidence': 'HIGH' if strength >= 80 else 'MEDIUM',
                        'details': {
                            'breakout_pct': breakout_pct,
                            'volume_ratio': volume_ratio,
                            'consolidation': consolidation
                        }
                    })

        # Cup and Handle Pattern
        if len(data) >= 60:
            prices = data['Close'].values

            # Find recent cup formation
            min_idx = np.argmin(prices[-40:-20]) + len(prices) - 40
            if min_idx > len(prices) - 25:
                left_side = prices[max(0, min_idx-20):min_idx]
                right_side = prices[min_idx:min_idx+10]

                if len(left_side) > 5 and len(right_side) > 2:
                    if left_side[0] > prices[min_idx] and right_side[-1] > prices[min_idx]:
                        cup_strength = min(100, 50 + (current_rsi/100) * 30)
                        patterns.append({
                            'type': 'Cup and Handle',
                            'strength': cup_strength,
                            'confidence': 'MEDIUM',
                            'details': {}
                        })

        # Flat Base Pattern
        if len(data) >= 40:
            recent = data['Close'].tail(30).values

            high_20 = np.max(recent[-20:])
            low_20 = np.min(recent[-20:])
            range_pct = ((high_20 - low_20) / low_20) * 100

            if range_pct < 8:  # Tight consolidation
                base_strength = min(100, 65 + (20 - range_pct) * 2)
                patterns.append({
                    'type': 'Flat Base Breakout',
                    'strength': base_strength,
                    'confidence': 'MEDIUM',
                    'details': {'consolidation_range': range_pct}
                })

        # Double Bottom Pattern
        if len(data) >= 40:
            prices = data['Close'].values
            recent_prices = prices[-40:]

            # Find two lows
            local_lows = []
            for i in range(5, len(recent_prices)-5):
                if recent_prices[i] < recent_prices[i-5:i].max() and \
                   recent_prices[i] < recent_prices[i+1:i+6].max():
                    local_lows.append((i, recent_prices[i]))

            if len(local_lows) >= 2:
                low1_idx, low1_val = local_lows[-2]
                low2_idx, low2_val = local_lows[-1]

                if abs(low1_val - low2_val) / low1_val < 0.05:  # Similar lows
                    double_bottom_strength = min(100, 70 + (current_rsi - 40) * 0.5)
                    patterns.append({
                        'type': 'Double Bottom',
                        'strength': double_bottom_strength,
                        'confidence': 'MEDIUM',
                        'details': {}
                    })

        # Filter by minimum strength
        min_strength = filters.get('pattern_strength_min', 65)
        patterns = [p for p in patterns if p['strength'] >= min_strength]

        return patterns

# ============================================================================
# TELEGRAM INTEGRATION
# ============================================================================

class TelegramSender:
    """Send messages to Telegram"""

    def __init__(self, token: str = None, chat_id: str = None):
        self.token = token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        self.enabled = bool(self.token and self.chat_id)

        if self.enabled:
            self.api_url = f"https://api.telegram.org/bot{self.token}/sendMessage"

    def send_message(self, message: str) -> bool:
        """Send a message to Telegram"""
        if not self.enabled:
            return False

        try:
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(self.api_url, data=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Telegram error: {str(e)}")
            return False

# ============================================================================
# MAIN SCANNING LOGIC
# ============================================================================

COMPLETE_NSE_FO_UNIVERSE = [
    '360ONE.NS', 'ABB.NS', 'APLAPOLLO.NS', 'AUBANK.NS', 'ADANIENSOL.NS',
    'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ABCAPITAL.NS', 'ALKEM.NS',
    'AMBER.NS', 'AMBUJACEM.NS', 'ANGELONE.NS', 'APOLLOHOSP.NS', 'ASHOKLEY.NS',
    'ASIANPAINT.NS', 'ASTRAL.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS',
    'BSE.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS',
    'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BDL.NS', 'BEL.NS',
    'BHARATFORG.NS', 'BHEL.NS', 'BPCL.NS', 'BHARTIARTL.NS', 'BIOCON.NS',
    'BLUESTARCO.NS', 'BOSCHLTD.NS', 'BRITANNIA.NS', 'CGPOWER.NS', 'CANBK.NS',
    'CDSL.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS',
    'COLPAL.NS', 'CAMS.NS', 'CONCOR.NS', 'CROMPTON.NS', 'CUMMINSIND.NS',
    'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DELHIVERY.NS', 'DIVISLAB.NS',
    'DIXON.NS', 'DRREDDY.NS', 'ETERNAL.NS', 'EICHERMOT.NS', 'EXIDEIND.NS',
    'NYKAA.NS', 'FORTIS.NS', 'GAIL.NS', 'GMRAIRPORT.NS', 'GLENMARK.NS',
    'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'HCLTECH.NS', 'HDFCAMC.NS',
    'HDFCBANK.NS', 'HDFCLIFE.NS', 'HAVELLS.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS',
    'HAL.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'HINDZINC.NS', 'POWERINDIA.NS',
    'HUDCO.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS',
    'IIFL.NS', 'ITC.NS', 'INDIANB.NS', 'IEX.NS', 'IOC.NS',
    'IRCTC.NS', 'IRFC.NS', 'IREDA.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS',
    'NAUKRI.NS', 'INFY.NS', 'INOXWIND.NS', 'INDIGO.NS', 'JINDALSTEL.NS',
    'JSWENERGY.NS', 'JSWSTEEL.NS', 'JIOFIN.NS', 'JUBLFOOD.NS', 'KEI.NS',
    'KPITTECH.NS', 'KALYANKJIL.NS', 'KAYNES.NS', 'KFINTECH.NS', 'KOTAKBANK.NS',
    'LTF.NS', 'LICHSGFIN.NS', 'LTIM.NS', 'LT.NS', 'LAURUSLABS.NS',
    'LICI.NS', 'LODHA.NS', 'LUPIN.NS', 'M&M.NS', 'MANAPPURAM.NS',
    'MANKIND.NS', 'MARICO.NS', 'MARUTI.NS', 'MFSL.NS', 'MAXHEALTH.NS',
    'MAZDOCK.NS', 'MPHASIS.NS', 'MCX.NS', 'MUTHOOTFIN.NS', 'NBCC.NS',
    'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NATIONALUM.NS', 'NESTLEIND.NS',
    'NUVAMA.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS',
    'OFSS.NS', 'POLICYBZR.NS', 'PGEL.NS', 'PIIND.NS', 'PNBHOUSING.NS',
    'PAGEIND.NS', 'PATANJALI.NS', 'PERSISTENT.NS', 'PETRONET.NS', 'PIDILITIND.NS',
    'PPLPHARMA.NS', 'POLYCAB.NS', 'PFC.NS', 'POWERGRID.NS', 'PREMIERENE.NS',
    'PRESTIGE.NS', 'PNB.NS', 'RBLBANK.NS', 'RECLTD.NS', 'RVNL.NS',
    'RELIANCE.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SHREECEM.NS', 'SRF.NS',
    'SAMMAANCAP.NS', 'MOTHERSON.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SOLARINDS.NS',
    'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUPREMEIND.NS',
    'SUZLON.NS', 'SWIGGY.NS', 'SYNGENE.NS', 'TATACONSUM.NS', 'TVSMOTOR.NS',
    'TCS.NS', 'TATAELXSI.NS', 'TMPV.NS', 'TATAPOWER.NS', 'TATASTEEL.NS',
    'TATATECH.NS', 'TECHM.NS', 'FEDERALBNK.NS', 'INDHOTEL.NS', 'PHOENIXLTD.NS',
    'TITAN.NS', 'TORNTPHARM.NS', 'TORNTPOWER.NS', 'TRENT.NS', 'TIINDIA.NS',
    'UNOMINDA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNIONBANK.NS', 'UNITDSPR.NS',
    'VBL.NS', 'VEDL.NS', 'IDEA.NS', 'VOLTAS.NS', 'WAAREEENER.NS',
    'WIPRO.NS', 'YESBANK.NS', 'ZYDUSLIFE.NS'
]

def run_scan(max_stocks=50, telegram_token=None, telegram_chat_id=None, export_excel=False):
    """Run the stock scan"""

    scanner = SimpleStockScanner()
    stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE[:max_stocks]

    filters = {
        'rsi_min': 30,
        'rsi_max': 75,
        'adx_min': 20,
        'min_volume_ratio': 1.2,
        'ma_support': True,
        'ma_type': 'SMA',
        'ma_tolerance': 3,
        'pattern_strength_min': 65
    }

    print(f"\n📊 Scanning {len(stocks_to_scan)} NSE F&O stocks...")
    print(f"Filters: RSI({filters['rsi_min']}-{filters['rsi_max']}) | ADX(>{filters['adx_min']}) | Vol(>{filters['min_volume_ratio']}x) | Strength(>{filters['pattern_strength_min']}%)\n")

    results = []

    for i, symbol in enumerate(stocks_to_scan):
        progress = (i + 1) / len(stocks_to_scan)
        bar = '█' * int(40 * progress) + '░' * int(40 * (1 - progress))
        clean_symbol = symbol.replace('.NS', '')
        print(f"\r[{bar}] {i+1}/{len(stocks_to_scan)} - {clean_symbol:<12}", end='', flush=True)

        try:
            # Get data
            data = scanner.get_stock_data(symbol)
            if data is None:
                continue

            # Check volume
            vol_ok, vol_ratio, vol_details = scanner.check_volume_criteria(data, filters['min_volume_ratio'])
            if not vol_ok:
                continue

            # Detect patterns
            patterns = scanner.detect_patterns(data, symbol, filters)
            if not patterns:
                continue

            # Get metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            results.append({
                'symbol': clean_symbol,
                'price': current_price,
                'volume_ratio': vol_ratio,
                'rsi': current_rsi,
                'adx': current_adx,
                'patterns': patterns,
                'strength': max(p['strength'] for p in patterns)
            })

        except Exception as e:
            continue

    # Clear progress
    print()

    # Sort by strength
    results.sort(key=lambda x: x['strength'], reverse=True)

    # Print results
    print(f"\n✅ Found {len(results)} qualifying stocks!\n")
    print("=" * 80)
    print("TOP QUALIFYING STOCKS")
    print("=" * 80)

    for idx, r in enumerate(results[:10], 1):
        print(f"{idx}. {r['symbol']:<8} | ₹{r['price']:>8.2f} | Vol: {r['volume_ratio']:>4.1f}x | RSI: {r['rsi']:>5.1f} | ADX: {r['adx']:>5.1f} | Strength: {r['strength']:>3.0f}%")

    if len(results) > 10:
        print(f"... and {len(results) - 10} more")

    # Send to Telegram
    if telegram_token and telegram_chat_id:
        telegram = TelegramSender(telegram_token, telegram_chat_id)

        ist = pytz.timezone('Asia/Kolkata')
        scan_time = datetime.now(ist).strftime('%d-%b %H:%M IST')

        message = f"""<b>📊 Stock Scanner Results</b>
<code>Time: {scan_time}
Found: {len(results)} stocks</code>

"""

        for idx, r in enumerate(results[:10], 1):
            patterns_str = ', '.join([p['type'] for p in r['patterns']][:2])
            message += f"""<b>{idx}. {r['symbol']}</b>
  Price: ₹{r['price']:.2f} | Vol: {r['volume_ratio']:.1f}x | RSI: {r['rsi']:.0f}
  Strength: {r['strength']:.0f}% | Patterns: {patterns_str}

"""

        if len(results) > 10:
            message += f"\n... and {len(results) - 10} more stocks"

        if telegram.send_message(message):
            print("\n✅ Message sent to Telegram!")
        else:
            print("\n❌ Failed to send Telegram message")

    return results

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='NSE F&O Stock Scanner')
    parser.add_argument('--max-stocks', type=int, default=50, help='Max stocks to scan')
    parser.add_argument('--telegram-token', default=os.getenv('TELEGRAM_BOT_TOKEN'))
    parser.add_argument('--telegram-chat-id', default=os.getenv('TELEGRAM_CHAT_ID'))

    args = parser.parse_args()

    results = run_scan(
        max_stocks=args.max_stocks,
        telegram_token=args.telegram_token,
        telegram_chat_id=args.telegram_chat_id
    )

    # Save results
    json_data = [{
        'symbol': r['symbol'],
        'price': round(r['price'], 2),
        'volume_ratio': round(r['volume_ratio'], 2),
        'rsi': round(r['rsi'], 1),
        'strength': round(r['strength'], 0),
        'patterns': [p['type'] for p in r['patterns']]
    } for r in results]

    filename = f"/tmp/claude-0/-home-user-nsepcs/b210c83d-264f-5c31-ad57-70612d00ce3b/scratchpad/scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(json_data, f, indent=2)

    print(f"\n💾 Results saved to: {filename}")
