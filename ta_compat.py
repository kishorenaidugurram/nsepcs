"""
Compatibility layer for TA library using pandas_ta
This allows streamlit_app.py to work even if 'ta' is not installed
"""

import pandas as pd
import pandas_ta as ta_lib

class RSIIndicator:
    def __init__(self, close):
        self.close = close
        self._rsi = ta_lib.rsi(close, length=14)

    def rsi(self):
        return self._rsi

class SMAIndicator:
    def __init__(self, close, window):
        self.close = close
        self.window = window
        self._sma = ta_lib.sma(close, length=window)

    def sma_indicator(self):
        return self._sma

class EMAIndicator:
    def __init__(self, close, window):
        self.close = close
        self.window = window
        self._ema = ta_lib.ema(close, length=window)

    def ema_indicator(self):
        return self._ema

class BollingerBands:
    def __init__(self, close, window=20, window_dev=2):
        self.close = close
        self.window = window
        self.window_dev = window_dev
        bb = ta_lib.bbands(close, length=window, std=window_dev)
        # Extract individual bands
        self._upper = bb.iloc[:, 2]  # Upper band
        self._middle = bb.iloc[:, 1] # Middle band (SMA)
        self._lower = bb.iloc[:, 0]  # Lower band

    def bollinger_hband(self):
        return self._upper

    def bollinger_mavg(self):
        return self._middle

    def bollinger_lband(self):
        return self._lower

class MACD:
    def __init__(self, close, window_fast=12, window_slow=26, window_sign=9):
        self.close = close
        self.macd_df = ta_lib.macd(close, fast=window_fast, slow=window_slow, signal=window_sign)
        # Columns are typically: MACD_12_26_9, MACDh_12_26_9, MACDs_12_26_9
        cols = self.macd_df.columns
        self._macd = self.macd_df.iloc[:, 0] if len(cols) > 0 else None
        self._signal = self.macd_df.iloc[:, 2] if len(cols) > 2 else None
        self._diff = self.macd_df.iloc[:, 1] if len(cols) > 1 else None

    def macd(self):
        return self._macd

    def macd_signal(self):
        return self._signal

    def macd_diff(self):
        return self._diff

class ADXIndicator:
    def __init__(self, high, low, close, window=14):
        self.high = high
        self.low = low
        self.close = close
        self._adx = ta_lib.adx(high, low, close, length=window)

    def adx(self):
        # ADX is typically the first column
        if isinstance(self._adx, pd.DataFrame):
            return self._adx.iloc[:, 0]
        return self._adx

class AverageTrueRange:
    def __init__(self, high, low, close, window=14):
        self.high = high
        self.low = low
        self.close = close
        self._atr = ta_lib.atr(high, low, close, length=window)

    def average_true_range(self):
        if isinstance(self._atr, pd.DataFrame):
            return self._atr.iloc[:, 0]
        return self._atr

class StochasticOscillator:
    def __init__(self, high, low, close, window=14, smooth_k=3, smooth_d=3):
        self.high = high
        self.low = low
        self.close = close
        stoch = ta_lib.stoch(high, low, close, k=window, d=smooth_d, smooth_k=smooth_k)
        if isinstance(stoch, pd.DataFrame):
            cols = stoch.columns
            self._stoch_k = stoch.iloc[:, 0] if len(cols) > 0 else None
            self._stoch_d = stoch.iloc[:, 1] if len(cols) > 1 else None
        else:
            self._stoch_k = stoch
            self._stoch_d = None

    def stoch(self):
        return self._stoch_k

    def stoch_signal(self):
        return self._stoch_d

class WilliamsRIndicator:
    def __init__(self, high, low, close, window=14):
        self.high = high
        self.low = low
        self.close = close
        self._williams_r = ta_lib.willr(high, low, close, length=window)

    def williams_r(self):
        return self._williams_r

# Create module-level namespace for compatibility
momentum = type('momentum', (), {
    'RSIIndicator': RSIIndicator,
    'StochasticOscillator': StochasticOscillator,
    'WilliamsRIndicator': WilliamsRIndicator,
})()

trend = type('trend', (), {
    'SMAIndicator': SMAIndicator,
    'EMAIndicator': EMAIndicator,
    'MACD': MACD,
    'ADXIndicator': ADXIndicator,
})()

volatility = type('volatility', (), {
    'BollingerBands': BollingerBands,
    'AverageTrueRange': AverageTrueRange,
})()
