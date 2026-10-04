#!/usr/bin/env python3
"""
Simple Standalone Stock Screening Script
Runs basic technical analysis on F&O stocks and sends results to Telegram
"""

import os
import asyncio
from datetime import datetime
import pytz
import pandas as pd
import numpy as np
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings

warnings.filterwarnings('ignore')

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# F&O Stock list (from streamlit_app.py)
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
    'IIFL.NS', 'ITC.NS', 'INDIANB.NS', 'IEX.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS',
    'IREDA.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'NAUKRI.NS', 'INFY.NS',
    'INOXWIND.NS', 'INDIGO.NS', 'JINDALSTEL.NS', 'JSWENERGY.NS', 'JSWSTEEL.NS',
    'JIOFIN.NS', 'JUBLFOOD.NS', 'KEI.NS', 'KPITTECH.NS', 'KALYANKJIL.NS',
    'KAYNES.NS', 'KFINTECH.NS', 'KOTAKBANK.NS', 'LTF.NS', 'LICHSGFIN.NS',
    'LTIM.NS', 'LT.NS', 'LAURUSLABS.NS', 'LICI.NS', 'LODHA.NS', 'LUPIN.NS',
    'M&M.NS', 'MANAPPURAM.NS', 'MANKIND.NS', 'MARICO.NS', 'MARUTI.NS', 'MFSL.NS',
    'MAXHEALTH.NS', 'MAZDOCK.NS', 'MPHASIS.NS', 'MCX.NS', 'MUTHOOTFIN.NS',
    'NBCC.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NATIONALUM.NS', 'NESTLEIND.NS',
    'NUVAMA.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'OFSS.NS',
    'POLICYBZR.NS', 'PGEL.NS', 'PIIND.NS', 'PNBHOUSING.NS', 'PAGEIND.NS',
    'PATANJALI.NS', 'PERSISTENT.NS', 'PETRONET.NS', 'PIDILITIND.NS', 'PPLPHARMA.NS',
    'POLYCAB.NS', 'PFC.NS', 'POWERGRID.NS', 'PREMIERENE.NS', 'PRESTIGE.NS',
    'PNB.NS', 'RBLBANK.NS', 'RECLTD.NS', 'RVNL.NS', 'RELIANCE.NS', 'SBICARD.NS',
    'SBILIFE.NS', 'SHREECEM.NS', 'SRF.NS', 'SAMMAANCAP.NS', 'MOTHERSON.NS',
    'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SOLARINDS.NS', 'SONACOMS.NS', 'SBIN.NS',
    'SAIL.NS', 'SUNPHARMA.NS', 'SUPREMEIND.NS', 'SUZLON.NS', 'SWIGGY.NS',
    'SYNGENE.NS', 'TATACONSUM.NS', 'TVSMOTOR.NS', 'TCS.NS', 'TATAELXSI.NS',
    'TMPV.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TATATECH.NS', 'TECHM.NS',
    'FEDERALBNK.NS', 'INDHOTEL.NS', 'PHOENIXLTD.NS', 'TITAN.NS', 'TORNTPHARM.NS',
    'TORNTPOWER.NS', 'TRENT.NS', 'TIINDIA.NS', 'UNOMINDA.NS', 'UPL.NS',
    'ULTRACEMCO.NS', 'UNIONBANK.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS',
    'IDEA.NS', 'VOLTAS.NS', 'WAAREEENER.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZYDUSLIFE.NS'
]

# Filter criteria
FILTER_CRITERIA = {
    'rsi_min': 30,
    'rsi_max': 75,
    'adx_min': 20,
    'volume_ratio_min': 1.2,
    'price_change_threshold': 1.0  # Stocks with >1% move
}


def calculate_rsi(prices, period=14):
    """Calculate RSI without external dependencies"""
    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down if down != 0 else 0
    rsi = 100 - 100 / (1 + rs) if rs != 0 else 50

    rsis = [rsi]
    for delta in deltas[period+1:]:
        if delta > 0:
            up = (up * (period - 1) + delta) / period
            down = (down * (period - 1)) / period
        else:
            up = (up * (period - 1)) / period
            down = (down * (period - 1) - delta) / period

        rs = up / down if down != 0 else 0
        rsi = 100 - 100 / (1 + rs) if rs != 0 else 50
        rsis.append(rsi)

    return rsis[-1] if rsis else 50


def calculate_adx(high, low, close, period=14):
    """Simplified ADX calculation"""
    try:
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean().iloc[-1]

        if atr == 0:
            return 50

        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0

        di_plus = (plus_dm.rolling(window=period).mean() / atr * 100).iloc[-1]
        di_minus = (minus_dm.rolling(window=period).mean() / atr * 100).iloc[-1]

        di_diff = abs(di_plus - di_minus)
        di_sum = di_plus + di_minus

        adx = 100 if di_sum == 0 else 100 * di_diff / di_sum
        return min(max(adx, 0), 100)
    except:
        return 50


def fetch_stock_data(symbol, period="3mo"):
    """Fetch stock data from Yahoo Finance"""
    try:
        data = yf.download(symbol, period=period, progress=False, timeout=10)
        if data.empty or len(data) < 30:
            return None
        return data
    except:
        return None


def analyze_stock(symbol):
    """Analyze a single stock"""
    try:
        data = fetch_stock_data(symbol)
        if data is None:
            return None

        # Current metrics
        current_price = data['Close'].iloc[-1]
        previous_close = data['Close'].iloc[-2]
        current_rsi = calculate_rsi(data['Close'].values, period=14)
        current_adx = calculate_adx(data['High'], data['Low'], data['Close'], period=14)

        # Volume analysis
        avg_volume_20 = data['Volume'].tail(20).mean()
        current_volume = data['Volume'].iloc[-1]
        volume_ratio = current_volume / avg_volume_20 if avg_volume_20 > 0 else 0

        # Price change
        price_change_pct = ((current_price - previous_close) / previous_close) * 100

        # Basic screening filters
        passes_rsi = FILTER_CRITERIA['rsi_min'] <= current_rsi <= FILTER_CRITERIA['rsi_max']
        passes_adx = current_adx >= FILTER_CRITERIA['adx_min']
        passes_volume = volume_ratio >= FILTER_CRITERIA['volume_ratio_min']
        passes_price = abs(price_change_pct) >= FILTER_CRITERIA['price_change_threshold']

        # Calculate a simple "strength" score
        strength = 0
        if passes_rsi:
            strength += 25
        if passes_adx:
            strength += 25
        if passes_volume:
            strength += 25
        if passes_price:
            strength += 25

        # Only return if passes basic filters
        if strength >= 50:
            return {
                'symbol': symbol,
                'clean_symbol': symbol.replace('.NS', ''),
                'current_price': current_price,
                'price_change': price_change_pct,
                'volume_ratio': volume_ratio,
                'rsi': current_rsi,
                'adx': current_adx,
                'strength': strength,
                'passes_rsi': passes_rsi,
                'passes_adx': passes_adx,
                'passes_volume': passes_volume,
                'passes_price': passes_price
            }

        return None

    except:
        return None


def run_screening(max_stocks=None):
    """Run screening on all stocks"""
    stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE

    if max_stocks:
        stocks_to_scan = stocks_to_scan[:max_stocks]

    print(f"\n📊 Screening {len(stocks_to_scan)} F&O stocks...")
    print(f"⚙️ Filters: RSI {FILTER_CRITERIA['rsi_min']}-{FILTER_CRITERIA['rsi_max']}, "
          f"ADX>{FILTER_CRITERIA['adx_min']}, Vol>{FILTER_CRITERIA['volume_ratio_min']}x\n")

    results = []

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(analyze_stock, symbol): symbol for symbol in stocks_to_scan}

        completed = 0
        for future in as_completed(futures):
            completed += 1
            try:
                result = future.result()
                if result:
                    results.append(result)
            except:
                pass

            if completed % 20 == 0 or completed == len(stocks_to_scan):
                print(f"Progress: {completed}/{len(stocks_to_scan)} ✓")

    # Sort by strength
    results.sort(key=lambda x: x['strength'], reverse=True)

    print(f"\n✅ Found {len(results)} stocks matching criteria\n")
    return results


def format_telegram_message(results):
    """Format results for Telegram"""
    if not results:
        return "❌ No stocks found matching the screening criteria today."

    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M IST')

    message = f"""
🎯 *NSE F&O Stock Screening Results*
━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 {current_time}
✅ Stocks Found: {len(results)}

*Filter Criteria:*
• RSI: {FILTER_CRITERIA['rsi_min']}-{FILTER_CRITERIA['rsi_max']}
• ADX: >{FILTER_CRITERIA['adx_min']}
• Volume: >{FILTER_CRITERIA['volume_ratio_min']}x
• Price Change: >{FILTER_CRITERIA['price_change_threshold']}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━
*Top 10 Stocks:*
"""

    for i, result in enumerate(results[:10], 1):
        symbol = result['clean_symbol']
        price = result['current_price']
        change = result['price_change']
        strength = result['strength']
        rsi = result['rsi']
        vol = result['volume_ratio']

        change_emoji = "📈" if change > 0 else "📉"

        message += f"\n{i}. *{symbol}* - ₹{price:.2f} {change_emoji}{change:+.2f}%"
        message += f"\n   Score: {strength}/100 | RSI: {rsi:.0f} | Vol: {vol:.1f}x"

    if len(results) > 10:
        message += f"\n\n... and {len(results) - 10} more stocks"

    message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    return message


async def send_telegram_message(message):
    """Send message to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False

    try:
        from telegram import Bot
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode='Markdown'
        )
        return True
    except Exception as e:
        print(f"Telegram error: {e}")
        return False


def export_to_csv(results):
    """Export results to CSV"""
    if not results:
        return None

    df = pd.DataFrame(results)
    df = df[[
        'clean_symbol', 'current_price', 'price_change', 'rsi', 'adx',
        'volume_ratio', 'strength'
    ]].sort_values('strength', ascending=False)

    filename = '/tmp/nsepcs_screening_results.csv'
    df.to_csv(filename, index=False)
    return df


def main():
    """Main execution"""
    print("\n" + "="*50)
    print("🚀 NSE F&O Stock Screening - Simple Edition")
    print("="*50)

    # Run screening
    results = run_screening()

    if results:
        # Export CSV
        df = export_to_csv(results)
        if df is not None:
            print(f"📊 Results exported to /tmp/nsepcs_screening_results.csv")
            print(f"\nTop 5 Results:")
            print(df.head(5).to_string())

        # Format and send Telegram
        message = format_telegram_message(results)
        print(f"\n📱 Message Preview:")
        print(message)

        # Send to Telegram if configured
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            sent = asyncio.run(send_telegram_message(message))
            if sent:
                print("\n✅ Message sent to Telegram!")
        else:
            print("\n⚠️  Telegram not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
    else:
        print("❌ No stocks found matching the criteria.")


if __name__ == "__main__":
    main()
