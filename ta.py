"""
Technical Analysis Indicators - Minimal implementation
Provides basic TA indicators when the 'ta' package is not available
"""

import pandas as pd
import numpy as np

class RSIIndicator:
    def __init__(self, close, window=14):
        self.close = close
        self.window = window

    def rsi(self):
        delta = self.close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

class SMAIndicator:
    def __init__(self, close, window):
        self.close = close
        self.window = window

    def sma_indicator(self):
        return self.close.rolling(window=self.window).mean()

class EMAIndicator:
    def __init__(self, close, window):
        self.close = close
        self.window = window

    def ema_indicator(self):
        return self.close.ewm(span=self.window).mean()

class BollingerBands:
    def __init__(self, close, window=20, std_dev=2):
        self.close = close
        self.window = window
        self.std_dev = std_dev

    def bollinger_mavg(self):
        return self.close.rolling(window=self.window).mean()

    def bollinger_hband(self):
        mid = self.close.rolling(window=self.window).mean()
        std = self.close.rolling(window=self.window).std()
        return mid + (std * self.std_dev)

    def bollinger_lband(self):
        mid = self.close.rolling(window=self.window).mean()
        std = self.close.rolling(window=self.window).std()
        return mid - (std * self.std_dev)

class MACD:
    def __init__(self, close, window_fast=12, window_slow=26, window_sign=9):
        self.close = close
        self.window_fast = window_fast
        self.window_slow = window_slow
        self.window_sign = window_sign

    def macd(self):
        ema_fast = self.close.ewm(span=self.window_fast).mean()
        ema_slow = self.close.ewm(span=self.window_slow).mean()
        return ema_fast - ema_slow

    def macd_signal(self):
        macd_line = self.macd()
        return macd_line.ewm(span=self.window_sign).mean()

    def macd_diff(self):
        return self.macd() - self.macd_signal()

class ADXIndicator:
    def __init__(self, high, low, close, window=14):
        self.high = high
        self.low = low
        self.close = close
        self.window = window

    def adx(self):
        plus_dm = self.high.diff().clip(lower=0)
        minus_dm = (-self.low.diff()).clip(lower=0)

        tr1 = self.high - self.low
        tr2 = (self.high - self.close.shift()).abs()
        tr3 = (self.low - self.close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        atr = tr.rolling(window=self.window).mean()

        di_plus = 100 * plus_dm.rolling(window=self.window).mean() / atr
        di_minus = 100 * minus_dm.rolling(window=self.window).mean() / atr

        dx = 100 * (di_plus - di_minus).abs() / (di_plus + di_minus)
        adx = dx.rolling(window=self.window).mean()

        return adx

class AverageTrueRange:
    def __init__(self, high, low, close, window=14):
        self.high = high
        self.low = low
        self.close = close
        self.window = window

    def average_true_range(self):
        tr1 = self.high - self.low
        tr2 = (self.high - self.close.shift()).abs()
        tr3 = (self.low - self.close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=self.window).mean()

class StochasticOscillator:
    def __init__(self, high, low, close, window=14):
        self.high = high
        self.low = low
        self.close = close
        self.window = window

    def stoch(self):
        low_min = self.low.rolling(window=self.window).min()
        high_max = self.high.rolling(window=self.window).max()
        k = 100 * (self.close - low_min) / (high_max - low_min)
        return k

class WilliamsRIndicator:
    def __init__(self, high, low, close, window=14):
        self.high = high
        self.low = low
        self.close = close
        self.window = window

    def williams_r(self):
        high_max = self.high.rolling(window=self.window).max()
        low_min = self.low.rolling(window=self.window).min()
        return -100 * (high_max - self.close) / (high_max - low_min)

# Module-level attributes to match ta package structure
class momentum:
    @staticmethod
    def RSIIndicator(close, window=14):
        return RSIIndicator(close, window)

    @staticmethod
    def StochasticOscillator(high, low, close, window=14):
        return StochasticOscillator(high, low, close, window)

    @staticmethod
    def WilliamsRIndicator(high, low, close, window=14):
        return WilliamsRIndicator(high, low, close, window)

class trend:
    @staticmethod
    def SMAIndicator(close, window):
        return SMAIndicator(close, window)

    @staticmethod
    def EMAIndicator(close, window):
        return EMAIndicator(close, window)

    @staticmethod
    def MACD(close, window_fast=12, window_slow=26, window_sign=9):
        return MACD(close, window_fast, window_slow, window_sign)

    @staticmethod
    def ADXIndicator(high, low, close, window=14):
        return ADXIndicator(high, low, close, window)

class volatility:
    @staticmethod
    def BollingerBands(close, window=20, std_dev=2):
        return BollingerBands(close, window, std_dev)

    @staticmethod
    def AverageTrueRange(high, low, close, window=14):
        return AverageTrueRange(high, low, close, window)
