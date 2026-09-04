"""
Technical Analysis Library Wrapper
Provides the same interface as the 'ta' library using numpy and pandas
"""

import numpy as np
import pandas as pd


class momentum:
    """Momentum indicators"""

    class RSIIndicator:
        def __init__(self, close, window=14):
            self.close = close
            self.window = window
            self._rsi = None

        def rsi(self):
            if self._rsi is None:
                delta = self.close.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=self.window).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=self.window).mean()
                rs = gain / loss
                self._rsi = 100 - (100 / (1 + rs))
            return self._rsi


class trend:
    """Trend indicators"""

    class ADXIndicator:
        def __init__(self, high, low, close, window=14):
            self.high = high
            self.low = low
            self.close = close
            self.window = window
            self._adx = None

        def adx(self):
            if self._adx is None:
                self._adx = calculate_adx(self.high, self.low, self.close, self.window)
            return self._adx

    class SMAIndicator:
        def __init__(self, close, window=20):
            self.close = close
            self.window = window
            self._sma = None

        def sma_indicator(self):
            if self._sma is None:
                self._sma = self.close.rolling(window=self.window).mean()
            return self._sma

    class EMAIndicator:
        def __init__(self, close, window=20):
            self.close = close
            self.window = window
            self._ema = None

        def ema_indicator(self):
            if self._ema is None:
                self._ema = self.close.ewm(span=self.window, adjust=False).mean()
            return self._ema

    class MACD:
        def __init__(self, close, window_fast=12, window_slow=26, window_sign=9):
            self.close = close
            self.window_fast = window_fast
            self.window_slow = window_slow
            self.window_sign = window_sign
            self._macd = None
            self._macd_signal = None

        def macd(self):
            if self._macd is None:
                ema_fast = self.close.ewm(span=self.window_fast, adjust=False).mean()
                ema_slow = self.close.ewm(span=self.window_slow, adjust=False).mean()
                self._macd = ema_fast - ema_slow
            return self._macd

        def macd_signal(self):
            if self._macd_signal is None:
                macd_line = self.macd()
                self._macd_signal = macd_line.ewm(span=self.window_sign, adjust=False).mean()
            return self._macd_signal


class volatility:
    """Volatility indicators"""

    class BollingerBands:
        def __init__(self, close, window=20, window_dev=2):
            self.close = close
            self.window = window
            self.window_dev = window_dev
            self._mavg = None
            self._hband = None
            self._lband = None

        def bollinger_mavg(self):
            if self._mavg is None:
                self._mavg = self.close.rolling(window=self.window).mean()
            return self._mavg

        def bollinger_hband(self):
            if self._hband is None:
                mavg = self.bollinger_mavg()
                std = self.close.rolling(window=self.window).std()
                self._hband = mavg + (self.window_dev * std)
            return self._hband

        def bollinger_lband(self):
            if self._lband is None:
                mavg = self.bollinger_mavg()
                std = self.close.rolling(window=self.window).std()
                self._lband = mavg - (self.window_dev * std)
            return self._lband


def calculate_adx(high, low, close, period=14):
    """Calculate Average Directional Index (ADX)"""

    # Calculate True Range
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # Calculate Directional Movements
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low

    pos_dm = pd.Series(0.0, index=high.index)
    neg_dm = pd.Series(0.0, index=high.index)

    for i in range(1, len(high)):
        if up_move.iloc[i] > down_move.iloc[i] and up_move.iloc[i] > 0:
            pos_dm.iloc[i] = up_move.iloc[i]
        if down_move.iloc[i] > up_move.iloc[i] and down_move.iloc[i] > 0:
            neg_dm.iloc[i] = down_move.iloc[i]

    # Calculate smoothed values
    atr = tr.rolling(window=period).mean()
    pos_di = (pos_dm.rolling(window=period).mean() / atr) * 100
    neg_di = (neg_dm.rolling(window=period).mean() / atr) * 100

    # Calculate ADX
    dx = (abs(pos_di - neg_di) / abs(pos_di + neg_di)) * 100
    adx = dx.rolling(window=period).mean()

    return adx
