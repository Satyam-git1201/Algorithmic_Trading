# -*- coding: utf-8 -*-
"""
Created on Fri Jun  4 06:51:25 2021

@author: kumar
"""
import yfinance as yf
import numpy as np
import datetime as dt
import pandas as pd
import matplotlib.pyplot as plt

ticker = 'AAPL'
ohlcv = yf.download(ticker,dt.date.today()-dt.timedelta(1825),dt.datetime.today())

def RSI(Data, n):
    df= ohlcv.copy()
    df['delta'] = df['Adj Close']-df['Adj Close'].shift(1)
    df['gain'] = np.where(df['delta']>=0,df['delta'],0)
    df['loss']=np.where(df['delta']<0, abs(df['delta']), 0)
    avg_gain=[]
    avg_loss=[]
    gain = df['gain'].tolist()
    loss = df['loss'].tolist()
    for i in range(len(df)):
        if i<n:
           avg_gain.append(np.nan)
           avg_loss.append(np.nan)
        elif i==n:
            avg_gain.append(df['gain'].rolling(n).mean().tolist()[n])
            avg_loss.append(df['loss'].rolling(n).mean().tolist()[n])
        else:
            avg_gain.append(((n-1)*avg_gain[i-1]+gain[i])/n)
            avg_loss.append(((n-1)*avg_loss[i-1]+loss[i])/n)
    df['Avg gain'] = np.array(avg_gain)
    df['Avg loss'] = np.array(avg_loss)
    df['RS'] = df['Avg gain']/df['Avg loss']
    df['RSI'] = 100 - 100/(1+df['RS'])
    return df['RSI']

rsi = RSI(ohlcv, 14)