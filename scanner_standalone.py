#!/usr/bin/env python3
"""
Standalone NSE F&O PCS Scanner - No dependencies on Streamlit
Runs stock pattern detection and sends results to Telegram
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta
import pytz
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import pandas as pd
    import numpy as np
    import yfinance as yf
    import requests
    print("✅ Core dependencies loaded")
except ImportError as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# NSE F&O Universe - 208 stocks
NSE_FO_STOCKS = [
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


class SimpleStockAnalyzer:
    """Simple stock analyzer using only pandas/numpy"""

    def __init__(self):
        self.ist = pytz.timezone('Asia/Kolkata')
        self.results = []

    def get_stock_data(self, symbol, period="3mo"):
        """Fetch stock data from Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)

            if len(data) < 20:
                return None

            # Add basic technical indicators using numpy/pandas only
            data['RSI'] = self._calculate_rsi(data['Close'])
            data['SMA_20'] = data['Close'].rolling(window=20).mean()
            data['SMA_50'] = data['Close'].rolling(window=50).mean()

            return data
        except Exception as e:
            return None

    def _calculate_rsi(self, prices, period=14):
        """Calculate RSI using pandas"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_adx(self, high, low, close, period=14):
        """Calculate ADX"""
        try:
            plus_dm = high.diff()
            minus_dm = -low.diff()

            plus_dm = plus_dm.where((plus_dm > 0) & (plus_dm > minus_dm), 0)
            minus_dm = minus_dm.where((minus_dm > 0) & (minus_dm > plus_dm), 0)

            tr = np.maximum(
                high - low,
                np.maximum(
                    abs(high - close.shift()),
                    abs(low - close.shift())
                )
            )

            atr = pd.Series(tr).rolling(window=period).mean()
            plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
            minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)

            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
            adx = dx.rolling(window=period).mean()

            return adx
        except:
            return None

    def analyze_stock(self, symbol):
        """Analyze a stock for potential patterns"""
        try:
            data = self.get_stock_data(symbol)
            if data is None:
                return None

            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            sma_20 = data['SMA_20'].iloc[-1]
            sma_50 = data['SMA_50'].iloc[-1]

            if pd.isna(current_rsi) or pd.isna(sma_20):
                return None

            # Basic pattern detection
            patterns = []
            strength = 0

            # Pattern 1: Price above both SMAs with good RSI
            if current_price > sma_20 > sma_50 and 30 <= current_rsi <= 75:
                patterns.append("Uptrend Formation")
                strength += 40

            # Pattern 2: Recent volume surge
            avg_volume = data['Volume'].tail(20).mean()
            current_volume = data['Volume'].iloc[-1]
            if current_volume > avg_volume * 1.5:
                patterns.append("Volume Breakout")
                strength += 30

            # Pattern 3: RSI in optimal range
            if 45 <= current_rsi <= 65:
                patterns.append("Optimal RSI Zone")
                strength += 20

            # Pattern 4: Distance from support
            support = data['Close'].tail(20).min()
            distance_from_support = ((current_price - support) / support) * 100
            if 10 <= distance_from_support <= 30:
                patterns.append("Support Distance")
                strength += 10

            if patterns and strength >= 65:
                return {
                    'symbol': symbol,
                    'price': current_price,
                    'rsi': current_rsi,
                    'patterns': patterns,
                    'strength': min(strength, 100),
                    'sma_20': sma_20,
                    'sma_50': sma_50,
                    'volume_ratio': current_volume / avg_volume
                }

            return None

        except Exception as e:
            return None

    def scan_all(self, stocks=None, max_workers=10):
        """Scan all stocks"""
        if stocks is None:
            stocks = NSE_FO_STOCKS

        print(f"\n🚀 Scanning {len(stocks)} stocks...")
        print(f"⏰ {datetime.now(self.ist).strftime('%Y-%m-%d %H:%M:%S IST')}")
        print("=" * 80)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.analyze_stock, symbol): symbol for symbol in stocks}

            completed = 0
            for future in as_completed(futures):
                completed += 1
                symbol = futures[future]
                try:
                    result = future.result()
                    if result:
                        self.results.append(result)
                        print(f"✅ [{completed:3d}/{len(stocks)}] {symbol:12} | Strength: {result['strength']:3.0f}% | {', '.join(result['patterns'][:2])}")
                    else:
                        print(f"⊘ [{completed:3d}/{len(stocks)}] {symbol:12} | No patterns")
                except Exception as e:
                    print(f"❌ [{completed:3d}/{len(stocks)}] {symbol:12} | Error")

        # Sort by strength
        self.results.sort(key=lambda x: x['strength'], reverse=True)

        print("=" * 80)
        print(f"✅ SCAN COMPLETE: {len(self.results)} stocks found\n")

        return self.results

    def get_telegram_message(self):
        """Format results for Telegram"""
        if not self.results:
            return "📊 **NSE PCS Scanner**\n\n❌ No patterns found today"

        msg = f"📊 **NSE PCS Scanner Report**\n"
        msg += f"⏰ {datetime.now(self.ist).strftime('%Y-%m-%d %H:%M IST')}\n"
        msg += f"✅ Found: {len(self.results)} stocks\n"
        msg += "=" * 50 + "\n\n"

        for i, r in enumerate(self.results[:15], 1):
            symbol = r['symbol'].replace('.NS', '')
            msg += f"{i}. **{symbol}** - ₹{r['price']:.2f}\n"
            msg += f"   💪 Strength: {r['strength']:.0f}% | RSI: {r['rsi']:.1f}\n"
            msg += f"   📍 {', '.join(r['patterns'][:2])}\n"
            msg += "\n"

        return msg


async def send_telegram(message, chat_id, token):
    """Send message via Telegram Bot API"""
    try:
        from telegram import Bot
        bot = Bot(token=token)
        await bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
        return True
    except Exception as e:
        print(f"⚠️  Telegram error: {e}")
        return False


def main():
    """Main execution"""
    print("\n" + "=" * 80)
    print("NSE F&O PCS SCANNER - STANDALONE")
    print("=" * 80)

    # Run scanner
    analyzer = SimpleStockAnalyzer()
    results = analyzer.scan_all(stocks=NSE_FO_STOCKS)

    # Display results
    if results:
        print("\n🏆 TOP RESULTS:")
        print("-" * 80)
        for i, r in enumerate(results[:10], 1):
            symbol = r['symbol'].replace('.NS', '')
            print(f"{i:2}. {symbol:12} | ₹{r['price']:8.2f} | RSI:{r['rsi']:5.1f} | "
                  f"Strength:{r['strength']:3.0f}% | Vol:{r['volume_ratio']:4.1f}x")

    # Save results
    report_time = datetime.now(analyzer.ist).strftime('%Y%m%d_%H%M%S')
    csv_file = f"/tmp/nse_scan_{report_time}.csv"

    if results:
        df = pd.DataFrame([{
            'Symbol': r['symbol'].replace('.NS', ''),
            'Price': r['price'],
            'RSI': r['rsi'],
            'Strength': r['strength'],
            'Patterns': ', '.join(r['patterns']),
            'Volume_Ratio': r['volume_ratio']
        } for r in results])

        df.to_csv(csv_file, index=False)
        print(f"\n📊 Results saved to: {csv_file}")

    # Telegram integration
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if token and chat_id:
        print("\n📱 Sending to Telegram...")
        message = analyzer.get_telegram_message()
        success = asyncio.run(send_telegram(message, chat_id, token))
        if success:
            print("✅ Message sent successfully!")
    else:
        print("\n⚠️  Telegram credentials not set")
        print("   Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to enable")
        print(f"   Results saved to: {csv_file}")

    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
