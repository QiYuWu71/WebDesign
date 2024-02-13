import sys
import os
sys.path.append(os.getcwd())
import flaskr
from flaskr.get_data import get_cur_price, get_his_prices,init_stock_data
from datetime import datetime as dt



def test_get_data():
    today = dt.today()
    start = dt(today.year-5, today.month, today.day)
    spy = get_his_prices("SPY", start_date=start, end_date=today)
    print(spy.head())






if __name__ == "__main__":
    #print(os.listdir())
    print(init_stock_data("SPY").head())