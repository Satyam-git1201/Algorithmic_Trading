# -*- coding: utf-8 -*-
"""
Created on Mon Jun  7 07:40:35 2021

@author: kumar
"""
import yfinance as yf
import numpy as np
import datetime as dt
import pandas as pd
import matplotlib.pyplot as plt

ticker = '^GSPC'
SnP = yf.download(ticker,dt.date.today()-dt.timedelta(1825),dt.datetime.today())

data = SnP
def CAGR(data):
    df = data.copy()
    df['Daily Returns']=df['Adj Close'].pct_change()
    df['cum_return'] = (1+df['Daily Returns']).cumprod()
    n = len(df)/252                         #number of trading days in a typical year
    CAGR = (df['cum_return'][-1])**(1/n) - 1
    return CAGR

def max_drawdown(data):
    df = data.copy()
    df['Daily Returns']=df['Adj Close'].pct_change()
    df['cum_return'] = (1+df['Daily Returns']).cumprod()
    df['cum_max'] = df['cum_return'].cummax()
    df['drawdown'] = df['cum_max']-df['cum_return']
    df['drawdown_per'] = df['drawdown']/df['cum_max']
    max_dd = df['drawdown_per'].max()
    return max_dd

def calmar(data):
    df=data.copy()
    clm = CAGR(df)/max_drawdown(df)
    return clm