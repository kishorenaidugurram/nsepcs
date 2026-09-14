"""
Mock ta module for technical analysis indicators
Uses pandas and numpy for basic implementations
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
    def __init__(self, close, window=20):
        self.close = close
        self.window = window

    def sma_indicator(self):
        return self.close.rolling(window=self.window).mean()

class EMAIndicator:
    def __init__(self, close, window=20):
        self.close = close
        self.window = window

    def ema_indicator(self):
        return self.close.ewm(span=self.window, adjust=False).mean()

class BollingerBands:
    def __init__(self, close, window=20, window_dev=2):
        self.close = close
        self.window = window
        self.window_dev = window_dev

    def bollinger_mavg(self):
        return self.close.rolling(window=self.window).mean()

    def bollinger_hband(self):
        sma = self.close.rolling(window=self.window).mean()
        std = self.close.rolling(window=self.window).std()
        return sma + (self.window_dev * std)

    def bollinger_lband(self):
        sma = self.close.rolling(window=self.window).mean()
        std = self.close.rolling(window=self.window).std()
        return sma - (self.window_dev * std)

class MACD:
    def __init__(self, close, window_slow=26, window_fast=12, window_sign=9):
        self.close = close
        self.window_slow = window_slow
        self.window_fast = window_fast
        self.window_sign = window_sign

    def macd(self):
        fast = self.close.ewm(span=self.window_fast, adjust=False).mean()
        slow = self.close.ewm(span=self.window_slow, adjust=False).mean()
        return fast - slow

    def macd_signal(self):
        fast = self.close.ewm(span=self.window_fast, adjust=False).mean()
        slow = self.close.ewm(span=self.window_slow, adjust=False).mean()
        macd_line = fast - slow
        return macd_line.ewm(span=self.window_sign, adjust=False).mean()

    def macd_diff(self):
        fast = self.close.ewm(span=self.window_fast, adjust=False).mean()
        slow = self.close.ewm(span=self.window_slow, adjust=False).mean()
        macd_line = fast - slow
        signal = macd_line.ewm(span=self.window_sign, adjust=False).mean()
        return macd_line - signal

class ADXIndicator:
    def __init__(self, high, low, close, window=14):
        self.high = high
        self.low = low
        self.close = close
        self.window = window

    def adx(self):
        plus_dm = np.zeros(len(self.high))
        minus_dm = np.zeros(len(self.high))

        for i in range(1, len(self.high)):
            up = self.high.iloc[i] - self.high.iloc[i-1]
            down = self.low.iloc[i-1] - self.low.iloc[i]

            if up > down and up > 0:
                plus_dm[i] = up
            if down > up and down > 0:
                minus_dm[i] = down

        tr = np.zeros(len(self.close))
        for i in range(1, len(self.close)):
            tr[i] = max(
                self.high.iloc[i] - self.low.iloc[i],
                abs(self.high.iloc[i] - self.close.iloc[i-1]),
                abs(self.low.iloc[i] - self.close.iloc[i-1])
            )

        atr = pd.Series(tr).rolling(window=self.window).mean()

        plus_di = 100 * pd.Series(plus_dm).rolling(window=self.window).mean() / atr
        minus_di = 100 * pd.Series(minus_dm).rolling(window=self.window).mean() / atr

        di_sum = plus_di + minus_di
        di_diff = abs(plus_di - minus_di)

        dx = 100 * di_diff / di_sum
        adx = dx.rolling(window=self.window).mean()

        return adx

class AverageTrueRange:
    def __init__(self, high, low, close, window=14):
        self.high = high
        self.low = low
        self.close = close
        self.window = window

    def average_true_range(self):
        tr = np.zeros(len(self.close))
        for i in range(1, len(self.close)):
            tr[i] = max(
                self.high.iloc[i] - self.low.iloc[i],
                abs(self.high.iloc[i] - self.close.iloc[i-1]),
                abs(self.low.iloc[i] - self.close.iloc[i-1])
            )
        return pd.Series(tr).rolling(window=self.window).mean()

class StochasticOscillator:
    def __init__(self, high, low, close, window=14):
        self.high = high
        self.low = low
        self.close = close
        self.window = window

    def stoch(self):
        lowest_low = self.low.rolling(window=self.window).min()
        highest_high = self.high.rolling(window=self.window).max()
        return 100 * (self.close - lowest_low) / (highest_high - lowest_low)

class WilliamsRIndicator:
    def __init__(self, high, low, close, window=14):
        self.high = high
        self.low = low
        self.close = close
        self.window = window

    def williams_r(self):
        highest = self.high.rolling(window=self.window).max()
        lowest = self.low.rolling(window=self.window).min()
        return -100 * (highest - self.close) / (highest - lowest)

# Create namespace-like structure
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
    def SMAIndicator(close, window=20):
        return SMAIndicator(close, window)

    @staticmethod
    def EMAIndicator(close, window=20):
        return EMAIndicator(close, window)

    @staticmethod
    def MACD(close, window_slow=26, window_fast=12, window_sign=9):
        return MACD(close, window_slow, window_fast, window_sign)

    @staticmethod
    def ADXIndicator(high, low, close, window=14):
        return ADXIndicator(high, low, close, window)

class volatility:
    @staticmethod
    def BollingerBands(close, window=20, window_dev=2):
        return BollingerBands(close, window, window_dev)

    @staticmethod
    def AverageTrueRange(high, low, close, window=14):
        return AverageTrueRange(high, low, close, window)
