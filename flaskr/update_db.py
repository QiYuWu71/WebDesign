from datetime import datetime as dt, timedelta
from flaskr.get_data import get_cur_price, init_stock_data, get_his_prices

def update_stock_data(db, symbol):
    """
    3.28:
    Update stock historical price data by today for a single stock
    """
    max_date = db.execute(
        "SELECT max(date_time) max_date "
        "FROM hist_price"
        " WHERE stock_symbol = ?", (symbol,)
    ).fetchone()

    max_date = dt.strptime(dict(max_date)['max_date'],"%Y-%m-%d %H:%M:%S")

    today = dt.today()
    if max_date.date() < today.date():
        updates = get_his_prices(symbol=symbol, start_date=max_date+timedelta(days=1), end_date=today)
        for row_index, row in updates.iterrows():
            db.execute(
            "INSERT INTO hist_price (stock_symbol, date_time, stock_price) VALUES (?, ?,?)",
            (symbol, dt.strftime(row['date'],"%Y-%m-%d %H:%M:%S"), row['price']),
            )
    

def update_index_data(db):
    """
    3.28:
    Update index historical price data by today for a single stock
    """
    max_date = db.execute(
        "SELECT max(date_time) FROM SPY"
    ).fetchone()

    max_date = db.execute(
        "SELECT max(date_time) max_date FROM SPY"
    ).fetchone()
   
    max_date = dt.strptime(dict(max_date)['max_date'],"%Y-%m-%d %H:%M:%S")
    today = dt.today()
    if max_date.date() < today.date():
 
        spy = get_his_prices(symbol="SPY", start_date=max_date+timedelta(days=1), end_date=today)
        for row_index, row in spy.iterrows():
            db.execute(
            "INSERT INTO SPY (date_time, index_value) VALUES (?, ?)",
            (dt.strftime(row['date'],"%Y-%m-%d %H:%M:%S"), row['price']),
            )

def init_hist(stock_symbol, db):
    """
    Initialize historical price data storage
    """
    hist_price = init_stock_data(stock_symbol)

    for row_index,row in hist_price.iterrows():
        db.execute(
            "INSERT INTO hist_price(stock_symbol,date_time,stock_price) VALUES (?,?,?)",
            (stock_symbol, dt.strftime(row['date'],"%Y-%m-%d %H:%M:%S"),row['price']),
        )


    