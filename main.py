import ccxt
import pandas as pd
import requests
import time
from ta.trend import MACD
import os

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

exchange = ccxt.binance()

def get_symbols():
    markets = exchange.load_markets()
    return [s for s in markets if s.endswith("/USDT")]

def get_data(symbol):
    ohlcv = exchange.fetch_ohlcv(symbol, '1h', limit=100)
    df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
    return df

def signal(df):
    macd = MACD(df['c'])
    df['macd'] = macd.macd()
    df['sig'] = macd.macd_signal()
    df['vavg'] = df['v'].rolling(10).mean()

    last = df.iloc[-1]
    prev = df.iloc[-2]

    vol_ok = last['v'] > last['vavg']

    golden = prev['macd'] < prev['sig'] and last['macd'] > last['sig']
    death = prev['macd'] > prev['sig'] and last['macd'] < last['sig']

    if vol_ok and golden:
        return "🟢 GOLDEN CROSS"
    if vol_ok and death:
        return "🔴 DEATH CROSS"
    return None

def run():
    symbols = get_symbols()

    for s in symbols:
        try:
            df = get_data(s)
            sig = signal(df)

            if sig:
                msg = f"""
🔥 SIGNAL

Coin: {s}
Type: {sig}
TF: 1H
"""
                send(msg)
                print(msg)

        except:
            continue

while True:
    run()
    time.sleep(300)