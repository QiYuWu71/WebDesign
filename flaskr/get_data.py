import requests
import pandas as pd
from flaskr.config import api_key
import json
from datetime import datetime as dt, date, timedelta
from dateutil.relativedelta import relativedelta
import pandas as pd
import numpy as np
import time
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0",
    "Accept-Encoding": "*",
    "Connection": "keep-alive",
    'Content-Type': 'application/json',
    'accept': 'application/json',
}

def get_company_name(stock_symbol):
    """get stock name using Alpha Vantage API, please add your own api_key to flaskr/config.py"""

    url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={stock_symbol}&apikey={api_key}'
    time.sleep(0.01)
    r = requests.get(url,headers=headers)
    data = r.json()
    name = data.get("Name")
    
    return name


def get_cur_price(stock_symbol):
    """get current data using Alpha Vantage API, please add your own api_key to flaskr/config.py"""

    url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={stock_symbol}&apikey={api_key}'
    time.sleep(0.01)
    r = requests.get(url,headers=headers)
    data = r.json()
    df = pd.DataFrame(data)

    return float(df.iloc[4][0])


def get_his_prices(symbol, start_date:dt, end_date:dt):
    """
    Get historical data of a stock/index between given start and end dates

    params:
    symbol:str stock symbol
    start:datetime start date in format of "yyyy-mm-dd"
    end:datetime end date in format of "yyyy-mm-dd"
    """
    symbol = symbol.upper()
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&outputsize=full&apikey={api_key}'
    time.sleep(0.01)
    r = requests.get(url,headers=headers)
   
    if start_date > end_date:
        raise ValueError("start date should be less than or equal to end date.")
    data = r.json()
    # print(data)
    if r.status_code == 200:
        price_data = data["Time Series (Daily)"]
        price_df = pd.DataFrame(price_data).transpose().reset_index()
        price_df.rename(columns={'index':'date'},inplace=True)
        price_df.loc[:,'date'] = [dt.strptime(d,'%Y-%m-%d') for d in price_df.date]
        
        price_df = price_df.loc[(price_df.date>=start_date)&(price_df.date<=end_date),["date", "5. adjusted close"]].reset_index(drop=True)
        price_df.rename(columns={"5. adjusted close":"price"}, inplace=True)
        price_df.sort_values(by='date',inplace=True)
        #his_prices = {"dates": dates, "prices": prices}
    
        return price_df

    else: return None


def init_stock_data(symbol):
    """
    Get 5 year history data for a stock/index from today(initialize historical data for a stock/index)
    """
    end = dt.today()
    start = end - relativedelta(years=5)
    price_data = get_his_prices(symbol=symbol, start_date=start, end_date=end)
    return price_data


def get_rf():
    """
    Get current risk free return
    """
    url = f'https://www.alphavantage.co/query?function=TREASURY_YIELD&interval=daily&maturity=10year&apikey={api_key}'
    time.sleep(0.01)
    r = requests.get(url,headers=headers)
    data = r.json()

    yield_data = pd.DataFrame(data['data'])
    rf = yield_data.iloc[0,1]
    rf = float(rf)

    return rf
