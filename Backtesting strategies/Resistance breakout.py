# -*- coding: utf-8 -*-
"""
Created on Tue Jun  8 13:46:42 2021

@author: kumar
"""
import numpy as np
import pandas as pd
from alpha_vantage.timeseries import TimeSeries
import copy
import time


def ATR(DF,n):
    "function to calculate True Range and Average True Range"
    df = DF.copy()
    df['H-L']=abs(df['High']-df['Low'])
    df['H-PC']=abs(df['High']-df['Close'].shift(1))
    df['L-PC']=abs(df['Low']-df['Close'].shift(1))
    df['TR']=df[['H-L','H-PC','L-PC']].max(axis=1,skipna=False)
    df['ATR'] = df['TR'].rolling(n).mean()
    #df['ATR'] = df['TR'].ewm(span=n,adjust=False,min_periods=n).mean()
    df2 = df.drop(['H-L','H-PC','L-PC'],axis=1)
    return df2['ATR']

def CAGR(DF):
    "function to calculate the Cumulative Annual Growth Rate of a trading strategy"
    df = DF.copy()
    df["cum_return"] = (1 + df["return"]).cumprod()
    n = len(df)/(252*78)
    CAGR = (df["cum_return"].tolist()[-1])**(1/n) - 1
    return CAGR

def volatility(DF):
    "function to calculate annualized volatility of a trading strategy"
    df = DF.copy()
    vol = df["return"].std() * np.sqrt(252*78)   #78 5-minute candles in regular trading hours on a single day
    return vol

def sharpe(DF,rf):
    "function to calculate sharpe ratio ; rf is the risk free rate"
    df = DF.copy()
    sr = (CAGR(df) - rf)/volatility(df)
    return sr
    

def max_drawdown(DF):
    "function to calculate max drawdown"
    df = DF.copy()
    df["cum_return"] = (1 + df["return"]).cumprod()
    df["cum_roll_max"] = df["cum_return"].cummax()
    df["drawdown"] = df["cum_roll_max"] - df["cum_return"]
    df["drawdown_pct"] = df["drawdown"]/df["cum_roll_max"]
    max_dd = df["drawdown_pct"].max()
    return max_dd

tickers = ["MSFT","AAPL","FB","AMZN","INTC", "CSCO","VZ","IBM","TSLA","AMD"]

ohlc_intraday = {} # directory with ohlc value for each stock   
api_call_count = 1
key_path = "C:\\Users\\kumar\\Documents\\alphavantageKey.txt"
ts = TimeSeries(key=open(key_path,'r').read(), output_format='pandas')
start_time = time.time()
for ticker in tickers:
    data = ts.get_intraday(symbol=ticker,interval='5min', outputsize='full')[0]
    api_call_count+=1
    data.columns = ["Open","High","Low","Close","Volume"]
    data = data.iloc[::-1]
    data = data.between_time('09:35', '16:00') #for removing the data outside regular trading hours
    ohlc_intraday[ticker] = data
    if api_call_count==5:
        api_call_count = 1
        time.sleep(60 - ((time.time() - start_time) % 60.0))

tickers = ohlc_intraday.keys()

ohlc_dict=copy.deepcopy(ohlc_intraday)
tickers_signal = {}
tickers_return = {}
for ticker in tickers:
    ohlc_dict[ticker]['ATR'] = ATR(ohlc_dict[ticker], 20)
    ohlc_dict[ticker]["rolling_max_cp"] = ohlc_dict[ticker]["High"].rolling(20).max()
    ohlc_dict[ticker]["rolling_min_cp"] = ohlc_dict[ticker]["Low"].rolling(20).min()
    ohlc_dict[ticker]["rolling_max_vol"] = ohlc_dict[ticker]["Volume"].rolling(20).max()
    ohlc_dict[ticker].dropna(inplace=True)
    tickers_signal[ticker] = ""
    tickers_return[ticker] = [0]
    
# For each ticker, identifying signal and calculating return
for ticker in tickers:
    for i in range(1, len(ohlc_dict[ticker])):
        if tickers_signal[ticker]=="":
            tickers_return[ticker].append(0)
            if ohlc_dict[ticker]['High'][i]>=ohlc_dict[ticker]['rolling_max_cp'][i] and \
              ohlc_dict[ticker]['Volume'][i]>1.5*ohlc_dict[ticker]['rolling_max_vol'][i-1]:
                  tickers_signal[ticker]="Buy"
            elif ohlc_dict[ticker]['Low'][i]<=ohlc_dict[ticker]['rolling_min_cp'][i] and \
              ohlc_dict[ticker]['Volume'][i]>1.5*ohlc_dict[ticker]['rolling_max_vol'][i-1]:
                  tickers_signal[ticker]="Sell"
          
            
        elif tickers_signal[ticker] == "Buy":
            if ohlc_dict[ticker]["Low"][i]<ohlc_dict[ticker]["Close"][i-1] - ohlc_dict[ticker]["ATR"][i-1]:
                tickers_signal[ticker] = ""
                tickers_return[ticker].append(((ohlc_dict[ticker]["Close"][i-1] - ohlc_dict[ticker]["ATR"][i-1])/ohlc_dict[ticker]["Close"][i-1])-1)
            elif ohlc_dict[ticker]["Low"][i]<=ohlc_dict[ticker]["rolling_min_cp"][i] and \
               ohlc_dict[ticker]["Volume"][i]>1.5*ohlc_dict[ticker]["rolling_max_vol"][i-1]:
                tickers_signal[ticker] = "Sell"
                tickers_return[ticker].append((ohlc_dict[ticker]["Close"][i]/ohlc_dict[ticker]["Close"][i-1])-1)
            else:
                tickers_return[ticker].append((ohlc_dict[ticker]["Close"][i]/ohlc_dict[ticker]["Close"][i-1])-1)
                
                
        elif tickers_signal[ticker] == "Sell":
            if ohlc_dict[ticker]["High"][i]>ohlc_dict[ticker]["Close"][i-1] + ohlc_dict[ticker]["ATR"][i-1]:
                tickers_signal[ticker] = ""
                tickers_return[ticker].append((ohlc_dict[ticker]["Close"][i-1]/(ohlc_dict[ticker]["Close"][i-1] + ohlc_dict[ticker]["ATR"][i-1]))-1)
            elif ohlc_dict[ticker]["High"][i]>=ohlc_dict[ticker]["rolling_max_cp"][i] and \
               ohlc_dict[ticker]["Volume"][i]>1.5*ohlc_dict[ticker]["rolling_max_vol"][i-1]:
                tickers_signal[ticker] = "Buy"
                tickers_return[ticker].append((ohlc_dict[ticker]["Close"][i-1]/ohlc_dict[ticker]["Close"][i])-1)
            else:
                tickers_return[ticker].append((ohlc_dict[ticker]["Close"][i-1]/ohlc_dict[ticker]["Close"][i])-1)
    ohlc_dict[ticker]['return'] = np.array(tickers_return[ticker])
    
#KPIs of this strategy
breakout = pd.DataFrame()
for ticker in tickers:
    breakout['ticker'] = ohlc_dict[ticker]['return']
breakout['return']=breakout.mean(axis=1)
print(CAGR(breakout))
print(sharpe(breakout, 0.025))
print(max_drawdown(breakout))

(1+breakout['return']).cumprod().plot()

#storing KPIs of individual stocks in separate dataframe
cagr = {}
sharpe_ratios = {}
max_dd = {}
for ticker in tickers:    
    cagr[ticker] =  CAGR(ohlc_dict[ticker])
    sharpe_ratios[ticker] =  sharpe(ohlc_dict[ticker],0.025)
    max_dd[ticker] =  max_drawdown(ohlc_dict[ticker])

KPI_data = pd.DataFrame([cagr,sharpe_ratios,max_dd],index=["Return","Sharpe Ratio","Max Drawdown"]) 

            
            

             
                
            
    


    

