#!/usr/bin/env python3
"""
Simplified standalone scanner script that runs without Streamlit or ta library.
Sends results to Telegram.
"""

import sys
import os
import json
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import pytz
import warnings
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.filterwarnings('ignore')

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

# Complete NSE F&O Universe
COMPLETE_NSE_FO_UNIVERSE = [
    '360ONE.NS', 'ABB.NS', 'APLAPOLLO.NS', 'AUBANK.NS', 'ADANIENSOL.NS', 'ADANIENT.NS',
    'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ABCAPITAL.NS', 'ALKEM.NS', 'AMBER.NS', 'AMBUJACEM.NS',
    'ANGELONE.NS', 'APOLLOHOSP.NS', 'ASHOKLEY.NS', 'ASIANPAINT.NS', 'ASTRAL.NS', 'AUROPHARMA.NS',
    'DMART.NS', 'AXISBANK.NS', 'BSE.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS',
    'BAJAJHLDNG.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BDL.NS', 'BEL.NS',
    'BHARATFORG.NS', 'BHEL.NS', 'BPCL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BLUESTARCO.NS',
    'BOSCHLTD.NS', 'BRITANNIA.NS', 'CGPOWER.NS', 'CANBK.NS', 'CDSL.NS', 'CHOLAFIN.NS',
    'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CAMS.NS', 'CONCOR.NS',
    'CROMPTON.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DELHIVERY.NS',
    'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'ETERNAL.NS', 'EICHERMOT.NS', 'EXIDEIND.NS',
    'NYKAA.NS', 'FORTIS.NS', 'GAIL.NS', 'GMRAIRPORT.NS', 'GLENMARK.NS', 'GODREJCP.NS',
    'GODREJPROP.NS', 'GRASIM.NS', 'HCLTECH.NS', 'HDFCAMC.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS',
    'HAVELLS.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HAL.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS',
    'HINDZINC.NS', 'POWERINDIA.NS', 'HUDCO.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS',
    'IDFCFIRSTB.NS', 'IIFL.NS', 'ITC.NS', 'INDIANB.NS', 'IEX.NS', 'IOC.NS',
    'IRCTC.NS', 'IRFC.NS', 'IREDA.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'NAUKRI.NS',
    'INFY.NS', 'INOXWIND.NS', 'INDIGO.NS', 'JINDALSTEL.NS', 'JSWENERGY.NS', 'JSWSTEEL.NS',
    'JIOFIN.NS', 'JUBLFOOD.NS', 'KEI.NS', 'KPITTECH.NS', 'KALYANKJIL.NS', 'KAYNES.NS',
    'KFINTECH.NS', 'KOTAKBANK.NS', 'LTF.NS', 'LICHSGFIN.NS', 'LTIM.NS', 'LT.NS',
    'LAURUSLABS.NS', 'LICI.NS', 'LODHA.NS', 'LUPIN.NS', 'M&M.NS', 'MANAPPURAM.NS',
    'MANKIND.NS', 'MARICO.NS', 'MARUTI.NS', 'MFSL.NS', 'MAXHEALTH.NS', 'MAZDOCK.NS',
    'MPHASIS.NS', 'MCX.NS', 'MUTHOOTFIN.NS', 'NBCC.NS', 'NHPC.NS', 'NMDC.NS',
    'NTPC.NS', 'NATIONALUM.NS', 'NESTLEIND.NS', 'NUVAMA.NS', 'OBEROIRLTY.NS', 'ONGC.NS',
    'OIL.NS', 'PAYTM.NS', 'OFSS.NS', 'POLICYBZR.NS', 'PGEL.NS', 'PIIND.NS',
    'PNBHOUSING.NS', 'PAGEIND.NS', 'PATANJALI.NS', 'PERSISTENT.NS', 'PETRONET.NS', 'PIDILITIND.NS',
    'PPLPHARMA.NS', 'POLYCAB.NS', 'PFC.NS', 'POWERGRID.NS', 'PREMIERENE.NS', 'PRESTIGE.NS',
    'PNB.NS', 'RBLBANK.NS', 'RECLTD.NS', 'RVNL.NS', 'RELIANCE.NS', 'SBICARD.NS',
    'SBILIFE.NS', 'SHREECEM.NS', 'SRF.NS', 'SAMMAANCAP.NS', 'MOTHERSON.NS', 'SHRIRAMFIN.NS',
    'SIEMENS.NS', 'SOLARINDS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS',
    'SUPREMEIND.NS', 'SUZLON.NS', 'SWIGGY.NS', 'SYNGENE.NS', 'TATACONSUM.NS', 'TVSMOTOR.NS',
    'TCS.NS', 'TATAELXSI.NS', 'TMPV.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TATATECH.NS',
    'TECHM.NS', 'FEDERALBNK.NS', 'INDHOTEL.NS', 'PHOENIXLTD.NS', 'TITAN.NS', 'TORNTPHARM.NS',
    'TORNTPOWER.NS', 'TRENT.NS', 'TIINDIA.NS', 'UNOMINDA.NS', 'UPL.NS', 'ULTRACEMCO.NS',
    'UNIONBANK.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'IDEA.NS', 'VOLTAS.NS',
    'WAAREEENER.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZYDUSLIFE.NS'
]

def calculate_rsi(data, period=14):
    """Calculate RSI indicator"""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_adx(high, low, close, period=14):
    """Calculate ADX indicator"""
    # True Range
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # Directional Movement
    up = (high - high.shift(1)) > (low.shift(1) - low)
    down = (low.shift(1) - low) > (high - high.shift(1))

    plus_dm = where(up & (high - high.shift(1) > 0), high - high.shift(1), 0)
    minus_dm = where(down & (low.shift(1) - low > 0), low.shift(1) - low, 0)

    # ATR
    atr = tr.rolling(period).mean()

    # DI
    plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr)

    # DX
    di_diff = abs(plus_di - minus_di)
    di_sum = plus_di + minus_di
    dx = 100 * (di_diff / di_sum)

    # ADX
    adx = dx.rolling(period).mean()
    return adx

def where(condition, true_val, false_val):
    """Numpy-like where function for pandas Series"""
    return pd.Series(np.where(condition, true_val, false_val), index=condition.index)

def fetch_stock_data(symbol, period="3mo"):
    """Fetch stock data from yfinance"""
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period=period, interval="1d")
        return data if len(data) >= 20 else None
    except:
        return None

class SimpleScanner:
    """Simple scanner without Streamlit or ta dependency"""

    def __init__(self):
        self.ist = pytz.timezone('Asia/Kolkata')

    def create_default_filters(self):
        """Create default filter configuration"""
        return {
            'stocks_to_scan': COMPLETE_NSE_FO_UNIVERSE,
            'rsi_min': 30,
            'rsi_max': 75,
            'adx_min': 20,
            'volume_ratio_min': 1.2,
            'min_price_change': 0.5,  # % change today
        }

    def scan_stocks(self, config, max_workers=4):
        """Scan stocks with given configuration"""
        results = []
        stocks = config['stocks_to_scan']

        print(f"[{datetime.now(self.ist).strftime('%H:%M:%S')}] Starting scan of {len(stocks)} stocks...")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._scan_single_stock, symbol, config): symbol
                for symbol in stocks
            }

            completed = 0
            for future in as_completed(futures):
                completed += 1
                symbol = futures[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                        print(f"[{completed}/{len(stocks)}] ✓ {symbol.replace('.NS', '')}")
                    else:
                        print(f"[{completed}/{len(stocks)}] - {symbol.replace('.NS', '')}")
                except Exception as e:
                    print(f"[{completed}/{len(stocks)}] ✗ {symbol.replace('.NS', '')} - {str(e)[:30]}")

        # Sort by volume ratio
        results.sort(key=lambda x: x['volume_ratio'], reverse=True)

        print(f"\n✅ Scan complete! Found {len(results)} stocks meeting criteria.\n")
        return results

    def _scan_single_stock(self, symbol, config):
        """Scan a single stock"""
        try:
            # Fetch stock data
            data = fetch_stock_data(symbol, period="3mo")
            if data is None or len(data) < 20:
                return None

            # Current day data
            current_day = data.iloc[-1]
            current_price = current_day['Close']
            current_volume = current_day['Volume']
            current_high = current_day['High']
            current_low = current_day['Low']

            # Previous day
            if len(data) >= 2:
                prev_price = data.iloc[-2]['Close']
                price_change_pct = ((current_price - prev_price) / prev_price) * 100
            else:
                price_change_pct = 0

            # Calculate technical indicators
            data['RSI'] = calculate_rsi(data['Close'])
            data['ADX'] = calculate_adx(data['High'], data['Low'], data['Close'])
            data['SMA_20'] = data['Close'].rolling(20).mean()

            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]
            sma_20 = data['SMA_20'].iloc[-1]

            # Apply basic filters
            if pd.isna(current_rsi) or pd.isna(current_adx):
                return None

            if not (config['rsi_min'] <= current_rsi <= config['rsi_max']):
                return None

            if current_adx < config['adx_min']:
                return None

            if current_price < sma_20 * 0.97:  # 3% below SMA
                return None

            # Volume check
            avg_20_volume = data['Volume'].tail(21).iloc[:-1].mean()
            volume_ratio = current_volume / avg_20_volume

            if volume_ratio < config['volume_ratio_min']:
                return None

            # Price action check - looking for bullish signals
            intraday_range = current_high - current_low
            close_position = ((current_price - current_low) / intraday_range) * 100 if intraday_range > 0 else 50

            # Strong bullish signal if closed in upper half of day's range
            if close_position < 40:
                return None

            # Calculate pattern strength based on multiple factors
            strength = 0

            # RSI signal
            if 40 <= current_rsi <= 70:
                strength += 30
            elif 30 <= current_rsi < 40:
                strength += 20

            # ADX signal
            if current_adx >= 25:
                strength += 25
            elif current_adx >= 20:
                strength += 15

            # Volume signal
            if volume_ratio >= 2.0:
                strength += 25
            elif volume_ratio >= 1.5:
                strength += 15

            # Price action signal
            if close_position >= 80:
                strength += 20
            elif close_position >= 60:
                strength += 10

            # Price change
            if price_change_pct >= 1.0:
                strength += 10

            if strength < 50:
                return None

            return {
                'symbol': symbol,
                'current_price': current_price,
                'rsi': current_rsi,
                'adx': current_adx,
                'volume_ratio': volume_ratio,
                'price_change': price_change_pct,
                'close_position': close_position,
                'strength': strength,
                'sma_20': sma_20,
            }

        except Exception as e:
            return None

    def send_to_telegram(self, results):
        """Send scan results to Telegram"""
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            print("⚠️  Telegram not configured. Skipping Telegram notification.")
            print("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables to enable.")
            return False

        try:
            # Format message
            timestamp = datetime.now(self.ist).strftime('%Y-%m-%d %H:%M:%S IST')
            message = f"📊 *NSE F&O PCS Scanner Results*\n"
            message += f"🕐 {timestamp}\n"
            message += f"✅ Found: *{len(results)} stocks*\n\n"
            message += "━━━━━━━━━━━━━━━━━━━━━\n"

            # Add top results (limit to 15 due to message length)
            for i, result in enumerate(results[:15], 1):
                symbol = result['symbol'].replace('.NS', '')
                price = result['current_price']
                rsi = result['rsi']
                adx = result['adx']
                strength = result['strength']

                message += f"\n{i}. *{symbol}* ₹{price:.2f}\n"
                message += f"   RSI:{rsi:.0f} ADX:{adx:.0f} Str:{strength:.0f}%\n"
                message += f"   Vol:{result['volume_ratio']:.1f}x ChgPct:{result['price_change']:.1f}%\n"

            if len(results) > 15:
                message += f"\n... and {len(results) - 15} more stocks\n"

            message += "\n━━━━━━━━━━━━━━━━━━━━━\n"
            message += "Run full scan for detailed analysis."

            # Send to Telegram
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                'chat_id': TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': 'Markdown'
            }

            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                print("✅ Results sent to Telegram successfully!")
                return True
            else:
                print(f"❌ Failed to send to Telegram: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error sending to Telegram: {str(e)}")
            return False

    def save_results_to_csv(self, results, filename=None):
        """Save results to CSV"""
        if not results:
            print("No results to save.")
            return None

        if filename is None:
            timestamp = datetime.now(self.ist).strftime('%Y%m%d_%H%M%S')
            filename = f"/tmp/claude-0/-home-user-nsepcs/017d6679-e0bc-5a5b-9f16-933803b74eb9/scratchpad/scanner_results_{timestamp}.csv"

        # Create output directory
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        # Prepare data
        data = []
        for result in results:
            data.append({
                'Symbol': result['symbol'].replace('.NS', ''),
                'Price': f"₹{result['current_price']:.2f}",
                'RSI': f"{result['rsi']:.1f}",
                'ADX': f"{result['adx']:.1f}",
                'Strength': f"{result['strength']:.0f}%",
                'Volume_Ratio': f"{result['volume_ratio']:.2f}x",
                'Price_Change_%': f"{result['price_change']:.2f}%",
                'Timestamp': datetime.now(self.ist).strftime('%Y-%m-%d %H:%M:%S IST')
            })

        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        print(f"📁 Results saved to: {filename}")
        return filename

    def print_summary(self, results):
        """Print a nice summary"""
        if not results:
            print("❌ No stocks found matching the criteria.")
            return

        print("\n" + "="*70)
        print("📊 SCAN RESULTS SUMMARY")
        print("="*70)
        print(f"Total Stocks Found: {len(results)}\n")

        for i, result in enumerate(results[:20], 1):
            symbol = result['symbol'].replace('.NS', '')
            price = result['current_price']
            rsi = result['rsi']
            adx = result['adx']
            strength = result['strength']
            vol_ratio = result['volume_ratio']
            price_chg = result['price_change']

            print(f"{i:2}. {symbol:12} ₹{price:9.2f} | RSI:{rsi:6.1f} ADX:{adx:6.1f}")
            print(f"    Strength:{strength:6.0f}% | Vol:{vol_ratio:5.2f}x | Chg:{price_chg:+6.2f}%\n")

        if len(results) > 20:
            print(f"... and {len(results) - 20} more stocks\n")

        print("="*70)


def main():
    """Main execution"""
    print("\n🚀 NSE F&O PCS Scanner - Automated Scan")
    print("="*70)

    # Initialize scanner
    scanner = SimpleScanner()

    # Create default configuration
    config = scanner.create_default_filters()

    # Run scan
    results = scanner.scan_stocks(config, max_workers=6)

    # Display summary
    scanner.print_summary(results)

    # Save results
    if results:
        csv_file = scanner.save_results_to_csv(results)

        # Send to Telegram
        scanner.send_to_telegram(results)

        print(f"\n✅ Scan completed successfully!")
        print(f"   📊 Found: {len(results)} stocks")
        print(f"   📁 Saved to: {csv_file}")
    else:
        print("\n⚠️  No stocks found matching the criteria.")

    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
