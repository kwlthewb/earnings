import os, math
import pandas as pd
import numpy as np
from sklearn import linear_model

# Data source
# Historical US stocks and earnings data: https://www.kaggle.com/tsaustin/us-historical-stock-prices-with-earnings-data
# Company details: https://www.kaggle.com/marketahead/all-us-stocks-tickers-company-info-logos to determine sector
# VIX performance: https://www.kaggle.com/tunguz/vix-cboe-volatility-index

# Thesis
# Using a three week stock returns sharpe ratio along with sector and VIX sharpe to produce signals on post-earnings stock performance
# Stocks with sector = Technology and (industry = Application Software or industry = Online Media), 377 stocks, are tested
# Tested with QQQ and VIX
# Linear Regression Formula: A * Stock_ThreeWeeks_Sharpe + B * Index_ThreeWeeks_Sharpe + C * VIX_ThreeWeeks_Sharpe = Post earnings one week mean daily return

# Further enhancements:
# Refine selection sector ETF via Beta
# Compute addition technical factors to signal strength or weakness in underlying money flow

def CalcAlpha(tickerPriceDF, edates, coefs):
    for idx in range(int(len(edates) * 0.7), len(edates)):
        eD = edates[idx]
        try:
            i = tickerPriceDF.index[tickerPriceDF['date'] == eD]
            j = indexPriceDF.index[indexPriceDF['date'] == eD]
            k = vixDF.index[vixDF['Date'] == eD]
            predicted = (coefs[0] * tickerPriceDF.iloc[i[0]-1]['Sharpe']) + (coefs[1] * indexPriceDF.iloc[j[0] - 1]['Sharpe']) + (coefs[2] * vixDF.iloc[k[0] - 1]['Sharpe'])
            print(eD + ' predicted average daily return: ' + str(predicted) + ' vs actual: ' + str(tickerPriceDF.iloc[i[0]+5]['MeanDailyRtr']))
        except:
            pass

compDetails = r'companies.csv'
stocksDF = pd.read_csv(compDetails)
stocksDF = stocksDF[['ticker','industry','sector']]
stocksDF = stocksDF.loc[(stocksDF['sector'] == 'Technology' ) & (stocksDF['industry'].isin(['Application Software','Online Media']))]

#print(stocksDF.shape[0])
stocks = stocksDF['ticker'].tolist()
stocks.append('AVID')
#### shortened list of stocks for sampling ######
stocks.append('QQQ')
#### shortened list of stocks for sampling ######

#print(stocks)
# Steps
# 1. price to return
# 2. Beta to index
# 3. two-weeks return using close and variance prior to earnings date
# 4. two-weeks return and variance relative to index prior to earnings date
# Output: one-week return post earnings date
priceDetails = r'stocks_latest\stock_prices_latest.csv'
earnsDetails = r'stocks_latest\earnings_latest.csv'

eDF = pd.read_csv(earnsDetails)
#print(eDF.shape[0])
eDF = eDF.loc[eDF['symbol'].isin(stocks)]
#print(eDF.columns)
#print(eDF.loc[eDF['symbol'] == 'GOOG'])
eDF.to_csv('filtered_earnings.csv')

pDF = pd.read_csv(priceDetails)
pDF = pDF.loc[pDF['symbol'].isin(stocks)]
pDF = pDF[['symbol','date','close']]
pDF['date'] = pd.to_datetime(pDF['date'])
sortedDF = pDF.sort_values(by=['symbol','date'])

rollingPeriod = 15
# compute stats for index security: QQQ
ticker = 'QQQ'
indexPriceDF = sortedDF[sortedDF['symbol'] == ticker]
indexPriceDF = indexPriceDF.reset_index(drop=True)
drtr = indexPriceDF['close'].pct_change()
wwrtr = indexPriceDF['close'].pct_change(periods=rollingPeriod)
indexPriceDF = indexPriceDF.merge(drtr.rename('dailyRtr'), left_index=True, right_index=True)
indexPriceDF = indexPriceDF.merge(wwrtr.rename('triWeeklyRtr'), left_index=True, right_index=True)
indexPriceDF['MeanClose'] = indexPriceDF['close'].rolling(rollingPeriod).mean()
indexPriceDF['MeanRtr'] = indexPriceDF['triWeeklyRtr'].rolling(rollingPeriod).mean()
indexPriceDF['StdRtr'] = indexPriceDF['triWeeklyRtr'].rolling(rollingPeriod).std()
indexPriceDF['Sharpe'] = indexPriceDF['MeanRtr'] / indexPriceDF['StdRtr']
indexPriceDF.to_csv('prices_index.csv')

#compute stats for VIX
vixDetails = r'vix-daily.csv'
vixDF = pd.read_csv(vixDetails)
vixDF = vixDF[['Date','VIX Close']]
vixDF['Date'] = pd.to_datetime(vixDF['Date'])
vixDF = vixDF.sort_values(by=['Date'])
drtr = vixDF['VIX Close'].pct_change()
wwrtr = vixDF['VIX Close'].pct_change(periods=rollingPeriod)
vixDF = vixDF.merge(drtr.rename('dailyRtr'), left_index=True, right_index=True)
vixDF = vixDF.merge(wwrtr.rename('triWeeklyRtr'), left_index=True, right_index=True)
vixDF['MeanRtr'] = vixDF['triWeeklyRtr'].rolling(rollingPeriod).mean()
vixDF['StdRtr'] = vixDF['triWeeklyRtr'].rolling(rollingPeriod).std()
vixDF['Sharpe'] = vixDF['MeanRtr'] / vixDF['StdRtr']
vixDF.to_csv('sorted_vix.csv')


# iterate through stocks in the list.
for ticker in stocks:
    if ticker == 'QQQ':
        continue
    # compute returns data
    tickerPriceDF = sortedDF[sortedDF['symbol'] == ticker]
    tickerPriceDF = tickerPriceDF.reset_index(drop=True)
    drtr = tickerPriceDF['close'].pct_change()
    wrtr = tickerPriceDF['close'].pct_change(periods=5)
    wwrtr = tickerPriceDF['close'].pct_change(periods=rollingPeriod)
    tickerPriceDF = tickerPriceDF.merge(drtr.rename('dailyRtr'), left_index=True, right_index=True)
    tickerPriceDF = tickerPriceDF.merge(wrtr.rename('weeklyRtr'), left_index=True, right_index=True)
    tickerPriceDF = tickerPriceDF.merge(wwrtr.rename('triWeeklyRtr'), left_index=True, right_index=True)
    tickerPriceDF['MeanDailyRtr'] = tickerPriceDF['dailyRtr'].rolling(5).mean()
    tickerPriceDF['MeanClose'] = tickerPriceDF['close'].rolling(rollingPeriod).mean()
    tickerPriceDF['MeanRtr'] = tickerPriceDF['triWeeklyRtr'].rolling(rollingPeriod).mean()
    tickerPriceDF['StdRtr'] = tickerPriceDF['triWeeklyRtr'].rolling(rollingPeriod).std()
    tickerPriceDF['Sharpe'] = tickerPriceDF['MeanRtr'] / tickerPriceDF['StdRtr']
    # iterate through earnings, 70% in-sample, 30% out-of-sample
    tickerEarnDF = eDF.loc[eDF['symbol'] == ticker][['symbol','date']]
    edates = tickerEarnDF['date'].tolist()
    print('Working on ' + ticker)
    #print(edates)
    # loop through earnings dates and get the respective slices
    ts = []
    for idx in range(0, int(len(edates) * 0.7)):
        eD = edates[idx]
        dd = {}
        try:
            # get stats on stock around earnings date
            i = tickerPriceDF.index[tickerPriceDF['date'] == eD]
            # get stats from index
            j = indexPriceDF.index[indexPriceDF['date'] == eD]
            # get stats from VIX
            k = vixDF.index[vixDF['Date'] == eD]
            # do the regression
            dd['StockSharpe'] = tickerPriceDF.iloc[i[0] - 1]['Sharpe']
            dd['IndexSharpe'] = indexPriceDF.iloc[j[0] - 1]['Sharpe']
            dd['VixSharpe'] = vixDF.iloc[k[0] - 1]['Sharpe']
            dd['StockRtr'] = tickerPriceDF.iloc[i[0]+5]['MeanDailyRtr']
            ts.append(dd)
        except:
            print('Error ' + ticker + ' ' + eD)
            pass
    regressDF = pd.DataFrame(ts)
    # save data for quality checks
    regressDF.to_csv('regress_' + ticker + '.csv')
    tickerPriceDF.to_csv('prices_' + ticker + '.csv')
    tickerEarnDF.to_csv('earnings_' + ticker + '.csv')

    # do linear regression on the three variables
    try:
        X = regressDF[['StockSharpe', 'IndexSharpe', 'VixSharpe']]
        y = regressDF[['StockRtr']]
        regr = linear_model.LinearRegression()
        regr.fit(X,y)
        CalcAlpha(tickerPriceDF,edates,np.array(regr.coef_[0]).tolist())
    except:
        pass


