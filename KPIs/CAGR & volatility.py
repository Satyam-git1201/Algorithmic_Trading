# -*- coding: utf-8 -*-
"""
Created on Mon Jun  7 06:19:58 2021

@author: kumar
"""
#Compound annual growth rate

import yfinance as yf
import numpy as np
import datetime as dt
import pandas as pd
import matplotlib.pyplot as plt

ticker = '^GSPC'
SnP = yf.download(ticker,dt.date.today()-dt.timedelta(1825),dt.datetime.today())

SnP['Adj Close'].plot()

def CAGR(data):
    df = data.copy()
    df['Daily Returns']=df['Adj Close'].pct_change()
    df['cum_return'] = (1+df['Daily Returns']).cumprod()
    n = len(df)/252                         #number of trading days in a typical year
    CAGR = (df['cum_return'][-1])**(1/n) - 1
    return CAGR

CAGR(SnP)

def volatility(data):
     df = data.copy()
     df['Daily Returns']=df['Adj Close'].pct_change()
     vol = df['Daily Returns'].std()*np.sqrt(252)
     return vol
volatility(SnP)
