# -*- coding: utf-8 -*-
"""
Created on Tue Jun  8 10:00:46 2021

@author: kumar
"""
import numpy as np
import pandas as pd
import yfinance as yf
import datetime as dt
import copy
import matplotlib.pyplot as plt

def CAGR(DF):
    df = DF.copy()
    df["cum_return"] = (1 + df["monthly_ret"]).cumprod()
    n = len(df)/12
    CAGR = (df["cum_return"].tolist()[-1])**(1/n) - 1
    return CAGR

def volatility(DF):
    df = DF.copy()
    vol = df["monthly_ret"].std() * np.sqrt(12)
    return vol

def sharpe(DF,rf):
    df = DF.copy()
    sr = (CAGR(df) - rf)/volatility(df)
    return sr
    

def max_drawdown(DF):
    df = DF.copy()
    df["cum_return"] = (1 + df["monthly_ret"]).cumprod()
    df["cum_roll_max"] = df["cum_return"].cummax()
    df["drawdown"] = df["cum_roll_max"] - df["cum_return"]
    df["drawdown_pct"] = df["drawdown"]/df["cum_roll_max"]
    max_dd = df["drawdown_pct"].max()
    return max_dd

#constituent stocks of Dow Jones Index
tickers = ["MMM","AXP","T","BA","CAT","CSCO","KO", "XOM","GE","GS","HD",
           "IBM","INTC","JNJ","JPM","MCD","MRK","MSFT","NKE","PFE","PG","TRV",
           "UNH","VZ","V","WMT","DIS"]

ohlc_dict = {}
start = dt.datetime.today()-dt.timedelta(3650)
end = dt.datetime.today()

#storing data for every stock in a dictionary
for ticker in tickers:
    print('Getting data for ', ticker)
    ohlc_dict[ticker] = yf.download(ticker,start,end,interval='1mo')
    ohlc_dict[ticker].dropna(inplace=True,how="all")

#Calculating and storing monthly return data for each stock in separate dataframe
tickers = ohlc_dict.keys()
ohlc_copy = copy.deepcopy(ohlc_dict)
Data = pd.DataFrame()
for ticker in tickers:
     ohlc_copy[ticker]['monthly_ret']=ohlc_copy[ticker]['Adj Close'].pct_change()  
     Data[ticker] = ohlc_copy[ticker]['monthly_ret']
Data.dropna(inplace = True)

#Calculating portfolio return

def portfolio(data, m, n):
    #m = number of stocks in portfolio
    #n = number of underperfomring stocks to be removed monthly
    df = data.copy()
    pf_tickers = []
    mon_ret = [0]
    for i in range(len(df)):
        if len(pf_tickers)>0:
            mon_ret.append(df[pf_tickers].iloc[i,:].mean())
            poor_stocks = df[pf_tickers].iloc[i,:].sort_values(ascending=True)[:n].index.values.tolist()
            pf_tickers = [t for t in pf_tickers if t not in poor_stocks]
        x = m-len(pf_tickers)
        new_stocks = df.iloc[i,:].sort_values(ascending=False)[:x].index.values.tolist()
        pf_tickers = pf_tickers + new_stocks
        print(pf_tickers)
    monthly_return_df = pd.DataFrame(np.array(mon_ret), columns=["monthly_ret"])
    return monthly_return_df

#KPIs for this strategy
print(CAGR(portfolio(Data, 6, 3)))
print(sharpe(portfolio(Data, 6, 3), 0.025))
print(max_drawdown(portfolio(Data, 6, 3)))

#KPIs for index buy and hold strategy during this period
DJI_data = yf.download('^DJI',start, end, interval='1mo')
DJI_data['monthly_ret'] = DJI_data['Adj Close'].pct_change().fillna(0)
print(CAGR(DJI_data))
print(sharpe(DJI_data, 0.025))
print(max_drawdown(DJI_data))


#Visualizations

fig, ax = plt.subplots()
plt.plot((1+portfolio(Data,6,3)).cumprod())
plt.plot((1+DJI_data["monthly_ret"].reset_index(drop=True)).cumprod())
plt.title("Index Return vs Strategy Return")
plt.ylabel("cumulative return")
plt.xlabel("months")
ax.legend(["Strategy Return","Index Return"])



    
            
            