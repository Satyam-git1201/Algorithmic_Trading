# -*- coding: utf-8 -*-
"""
Created on Thu Jun 10 19:48:07 2021

@author: kumar
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd

tickers = ["AXP","AAPL","BA","CAT","CVX","CSCO","DIS","DOW", "XOM",
           "HD","IBM","INTC","JNJ","KO","MCD","MMM","MRK","MSFT",
           "NKE","PFE","PG","TRV","UTX","UNH","VZ","V","WMT","WBA"]

financial_dir = {}

for ticker in tickers:
    try:
    #getting balance sheet data from yahoo finance for the given ticker
        temp_dir = {}
        url = 'https://in.finance.yahoo.com/quote/'+ticker+'/balance-sheet?p='+ticker
        page = requests.get(url)
        page_content = page.content
        soup = BeautifulSoup(page_content,'html.parser')
        tabl = soup.find_all("div", {"class" : "M(0) Whs(n) BdEnd Bdc($seperatorColor) D(itb)"})
        for t in tabl:
            rows = t.find_all("div", {"class" : "rw-expnded"})
            for row in rows:
                temp_dir[row.get_text(separator='|').split("|")[0]]=row.get_text(separator='|').split("|")[1]
        
        #getting income statement data from yahoo finance for the given ticker
        url = 'https://in.finance.yahoo.com/quote/'+ticker+'/financials?p='+ticker
        page = requests.get(url)
        page_content = page.content
        soup = BeautifulSoup(page_content,'html.parser')
        tabl = soup.find_all("div", {"class" : "M(0) Whs(n) BdEnd Bdc($seperatorColor) D(itb)"})
        for t in tabl:
            rows = t.find_all("div", {"class" : "rw-expnded"})
            for row in rows:
                temp_dir[row.get_text(separator='|').split("|")[0]]=row.get_text(separator='|').split("|")[1]
        
        #getting cashflow statement data from yahoo finance for the given ticker
        url = 'https://in.finance.yahoo.com/quote/'+ticker+'/cash-flow?p='+ticker
        page = requests.get(url)
        page_content = page.content
        soup = BeautifulSoup(page_content,'html.parser')
        tabl = soup.find_all("div", {"class" : "M(0) Whs(n) BdEnd Bdc($seperatorColor) D(itb)"})
        for t in tabl:
            rows = t.find_all("div", {"class" : "rw-expnded"})
            for row in rows:
                temp_dir[row.get_text(separator='|').split("|")[0]]=row.get_text(separator='|').split("|")[1]
        
        #getting key statistics data from yahoo finance for the given ticker
        url = 'https://in.finance.yahoo.com/quote/'+ticker+'/key-statistics?p='+ticker
        page = requests.get(url)
        page_content = page.content
        soup = BeautifulSoup(page_content,'html.parser')
        tabl = soup.findAll("div", {"class": "Mstart(a) Mend(a)"}) # try soup.findAll("table") if this line gives error 
        for t in tabl:
            rows = t.find_all("tr")
            for row in rows:
                if len(row.get_text(separator='|').split("|")[0:2])>0:
                    temp_dir[row.get_text(separator='|').split("|")[0]]=row.get_text(separator='|').split("|")[-1]    
        
        #combining all extracted information with the corresponding ticker
        financial_dir[ticker] = temp_dir
    except:
        print("Could not scrap the data for ",ticker)
    
    
financial_data = pd.DataFrame(financial_dir)
financial_data.dropna(how='all',axis=1,inplace=True)
tickers = financial_data.columns 
for ticker in tickers:
    financial_data = financial_data[~financial_data[ticker].str.contains("[a-z]").fillna(False)]
  
#selected information    
stats = ["EBITDA",
         "Depreciation & amortisation",
         "Market cap (intra-day)",
         "Net income available to common shareholders",
         "Net cash provided by operating activities",
         "Capital expenditure",
         "Total current assets",
         "Total current liabilities",
         "Net property, plant and equipment",
         "Total stockholders' equity",
         "Long-term debt",
         "Forward annual dividend yield"]

#renaming index values suitably
indx_values = ["EBITDA","D&A","MarketCap","NetIncome","CashFlowOps","Capex","CurrAsset",
        "CurrLiab","PPE","BookValue","TotDebt","DivYield"]
all_stats = {}
for ticker in tickers:
    try:
        temp = financial_data[ticker]
        ticker_stats = []
        for stat in stats:
            ticker_stats.append(temp.loc[stat])
        all_stats['{}'.format(ticker)] = ticker_stats
    except:
        print("can't read data for ",ticker)


#Cleaning the data and converting it to numeric values
all_stats_df = pd.DataFrame(all_stats,index=indx_values)
all_stats_df[tickers] = all_stats_df[tickers].replace({',': ''}, regex=True)
all_stats_df[tickers] = all_stats_df[tickers].replace({'M': 'E+03'}, regex=True)
all_stats_df[tickers] = all_stats_df[tickers].replace({'B': 'E+06'}, regex=True)
all_stats_df[tickers] = all_stats_df[tickers].replace({'T': 'E+09'}, regex=True)
all_stats_df[tickers] = all_stats_df[tickers].replace({'%': 'E-02'}, regex=True)
for ticker in all_stats_df.columns:
    all_stats_df[ticker] = pd.to_numeric(all_stats_df[ticker].values,errors='coerce')
all_stats_df.dropna(axis=1,inplace=True)
tickers = all_stats_df.columns


#Calculating and storing important data in separate dataframe
transpose_df = all_stats_df.transpose()
result_df = pd.DataFrame()
result_df["EBIT"] = transpose_df["EBITDA"] - transpose_df["D&A"]
result_df["TEV"] =  transpose_df["MarketCap"].fillna(0) \
                         +transpose_df["TotDebt"].fillna(0) \
                         -(transpose_df["CurrAsset"].fillna(0)-transpose_df["CurrLiab"].fillna(0))
result_df["EarningYield"] =  final_stats_df["EBIT"]/final_stats_df["TEV"]
result_df["FCFYield"] = (transpose_df["CashFlowOps"]-transpose_df["Capex"])/transpose_df["MarketCap"]
result_df["ROC"]  = (transpose_df["EBITDA"] - transpose_df["D&A"])/(transpose_df["PPE"]+transpose_df["CurrAsset"]-transpose_df["CurrLiab"])
result_df["BookToMkt"] = transpose_df["BookValue"]/transpose_df["MarketCap"]
result_df["DivYield"] = transpose_df["DivYield"]

# ranking stocks based on Magic Formula
result_copy = result_df.loc[tickers,:]
result_copy["CombRank"] = result_copy["EarningYield"].rank(ascending=False,na_option='bottom')+final_stats_val_df["ROC"].rank(ascending=False,na_option='bottom')
result_copy["MagicFormulaRank"] = result_copy["CombRank"].rank(method='first')
value_stocks = result_copy.sort_values("MagicFormulaRank").iloc[:,[2,4,8]]
print('/                                           /')
print("Value stocks based on Greenblatt's Magic Formula")
print('/                                           /')
print(value_stocks)


# ranking stocks based on dividend yield
high_dividend_stocks = result_df.sort_values("DivYield",ascending=False).iloc[:,6]
print('/                                           /')
print("Highest dividend paying stocks")
print('/                                           /')
print(high_dividend_stocks)


# Magic Formula & Dividend yield combined
result_df["CombRank"] = result_df["EarningYield"].rank(ascending=False,method='first') \
                              +result_df["ROC"].rank(ascending=False,method='first')  \
                              +result_df["DivYield"].rank(ascending=False,method='first')
result_df["CombinedRank"] = result_df["CombRank"].rank(method='first')
value_high_div_stocks = result_df.sort_values("CombinedRank").iloc[:,[2,4,6,8]]
print('/                                           /')
print("Magic Formula and Dividend Yield combined")
print('/                                           /')
print(value_high_div_stocks)


