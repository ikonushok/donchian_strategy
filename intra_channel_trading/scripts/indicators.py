import pandas as pd

def calculate_donchian(data, donchian_window):
    dataset = data.copy()
    dataset['Upper'] = dataset['High'].rolling(donchian_window).max()
    dataset['Lower'] = dataset['Low'].rolling(donchian_window).min()
    dataset[['Upper', 'Lower']] = dataset[['Upper', 'Lower']].shift(1)
    return dataset

def calculate_rsi(data, rsi_period):
    dataset = data.copy()
    delta = dataset['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    dataset['RSI'] = rsi
    dataset['RSI'] = dataset['RSI'].shift(1)
    return dataset

def calculate_atr(data, atr_period):
    dataset = data.copy()
    tr = pd.concat([
        dataset['High'] - dataset['Low'],
        (dataset['High'] - dataset['Close'].shift()).abs(),
        (dataset['Low'] - dataset['Close'].shift()).abs()
    ], axis=1).max(axis=1)
    dataset['ATR'] = tr.rolling(atr_period).mean()
    dataset['ATR'] = dataset['ATR'].shift(1)
    return dataset
