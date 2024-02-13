import pandas as pd
from datetime import datetime as dt, timedelta
from flaskr.update_db import update_stock_data
from flaskr.get_data import get_cur_price, get_company_name
from flaskr.db import get_db
from dateutil.relativedelta import relativedelta


def user_stock(user_id):
    """
    Get stock list for a user
    Param:
    user_id:int user_id
    
    Return:
    Dataframe 
    columns: stock

    """
    db = get_db()
    stocks = db.execute("SELECT stock_symbol, total_shares shares FROM stock WHERE author_id=?" ,(user_id,)).fetchall()
    db.commit()
    results = pd.DataFrame()
    if len(stocks)==0:
        return pd.DataFrame()
    for stock in stocks:
        stock = dict(stock)
        curr_price = get_cur_price(stock["stock_symbol"])
        stock["curr_price"] = curr_price
    
        results = results.append(stock,ignore_index=True)

    results.set_index('stock_symbol',inplace=True)
    results = results.transpose()

    return results


def all_stock():
    """
    Get stock list for all users
    
    Return:
    Dataframe 
    columns: 
    user_id:int
    username: str
    stock_symbol: str
    shares:int shares held by this user
    """
    db = get_db()
    stocks = db.execute(
        "SELECT u.id, u.username username, s.stock_symbol stock_symbol, s.stock_name, s.total_shares shares"
        " FROM stock s LEFT JOIN user u ON s.author_id = u.id"
        " ORDER BY author_id"
        ).fetchall()
    db.commit()
    results = pd.DataFrame(columns=['id','username','stock_symbol','shares','curr_price'])
    if len(stocks)==0:
        return pd.DataFrame()
    for stock in stocks:
        stock = dict(stock)
        curr_price = get_cur_price(stock["stock_symbol"])
        stock["curr_price"] = curr_price
        
        stock = pd.DataFrame(stock,index=[0])
   
        results = pd.concat([results, stock],ignore_index=True)

    return results

def get_his_from_db(symbol):
    """
    Get historical data from database for a single stock
    """
    db = get_db()
    today = dt.today()
    start = today - relativedelta(years=5)

    stock_query = db.execute("SELECT date_time, stock_price FROM hist_price "
            "WHERE stock_symbol=? ORDER BY date_time" , (symbol,))
    df = pd.DataFrame.from_records(data = stock_query.fetchall(), columns=['date','price'])
    df = df.loc[(df.date>=start)&(df.date<=today), :]
    df.set_index('date', inplace=True)
    df.columns = [symbol]
    db.commit()
    return df

def get_price_df(stock_list):
    """
    Get historical price data for a list of stocks and return as Dataframe
    """
    df = pd.DataFrame()
    if len(stock_list) == 0:
        return df
    for stock in stock_list:
        stock_price = get_his_from_db(stock)
        df = df.join(stock_price, how='right', lsuffix='_left', rsuffix='_right') # add lsuffix and rsuffix to avoid valueerror of "column overlap but no suffix specified"
    
    return df

def get_cur_user(db, g):
    """Get current user name and balance from database, table user"""

    user = db.execute(
        "SELECT username, balance"
        " FROM user"
        " WHERE id = ?", (g.user["id"],)
    ).fetchall()
    u_dict = {} # user name and balance dictionary, forward to index.html and display on website
    for u in user:
        # sqlite3.Row to dict
        u_dict = dict(u)
        u_dict['balance'] = round(u_dict['balance'],2)
    return u_dict


def get_stocks_for_cur_user(db, g):
    """Get stocks for current users
    
    Return:
    stock.sqlite
    stock list
    """
    stocks = db.execute(
        "SELECT stock_symbol, stock_name, total_shares"
        " FROM stock s JOIN user u ON s.author_id = u.id"
        " WHERE id = ?"
        " ORDER BY stock_id DESC", (g.user["id"],) # DESC to match the order of tracks
    ).fetchall()
    stock_name_list = []
    stock_symbol_list = []
    s_list = [] # stock dict

    # get a stock dict of the current user, the logic is same as above
    for s in stocks:
        # sqlite3.Row to dict
        s_dict = dict(s)
        company_name = get_company_name(s["stock_name"])
        s_dict["stock_name"] = company_name
        update_stock_data(db, s["stock_symbol"])

        stock_name_list.append(s["stock_name"])
        stock_symbol_list.append(s["stock_symbol"])
        s_list.append(s_dict)

    return stocks, s_list, stock_symbol_list

def get_tracks_for_cur_user(db, g, stock_symbol_list):
    """
    get current user stock buy/sell track from database, table track
    get current price and price change, save track information to track_list, forward to index.html and display on website
    get lists used to plot a bar chart

    Return:
    track_list
    stock_symbol_list
    track_price_list
    cur_price_list
    holding_list
    """
    tracks = db.execute(
        "SELECT track_id, stock_symbol, stock_name, date_time, track_price, num_share, author_id, username, buy_or_sell"
        " FROM track t JOIN user u ON t.author_id = u.id"
        " WHERE u.id = ?"
        " ORDER BY track_id DESC", (g.user["id"],)
    ).fetchall()
    # get current price and price change, save track information to track_list, forward to index.html and display on website
    track_list = []

    # lists used to plot a bar chart
    track_price_list = []
    cur_price_list = []
    holding_list = []
    temp_stock_symbol = [i for i in stock_symbol_list]
    i = 0 # user index to help make sure the order of elements in other lists match the stock symbol list
    
    for track in tracks:
        # sqlite3.Row to dict
        tracks_dict = dict(track)
        cur_price = get_cur_price(track["stock_symbol"])
        tracks_dict["current_price"] = cur_price
        company_name = get_company_name(track["stock_symbol"])
        tracks_dict["stock_name"] = company_name
        price_change = float(cur_price) / track["track_price"] - 1
        tracks_dict["price_change"] = str(round(price_change * 100, 2))+"%"
        holding = track["num_share"] * float(cur_price)
        if tracks_dict["buy_or_sell"] == 1:
            tracks_dict["buy_or_sell"] = "BUY"
        else:
            tracks_dict["buy_or_sell"] = "SELL"
            
        if track["author_id"] == g.user["id"]:
            # update stock historical data
            track_list.append(tracks_dict)
            
            # if user holds the stock, plot the comparison of the latest buy/sell price with the current price
            if track["stock_symbol"] == temp_stock_symbol[i]:
                track_price_list.append(track["track_price"])
                cur_price_list.append(cur_price)
                holding_list.append(float(holding))
                i += 1

    return track_list, track_price_list, cur_price_list, holding_list

def get_tracks_for_all_user(db):
    tracks = db.execute(
        "SELECT track_id, author_id, username, stock_symbol, stock_name, date_time, track_price, num_share, author_id, username, buy_or_sell"
        " FROM track t JOIN user u ON t.author_id = u.id"
        " WHERE DATE(date_time) = date('now')"
        " ORDER BY author_id ASC, track_id DESC"
    ).fetchall()
    # get current price and price change, save track information to track_list, forward to index.html and display on website
    track_list = []
    
    for track in tracks:
        # sqlite3.Row to dict
        tracks_dict = dict(track)
        print(tracks_dict)
        cur_price = get_cur_price(track["stock_symbol"])
        tracks_dict["current_price"] = cur_price
        company_name = get_company_name(track["stock_symbol"])
        tracks_dict["stock_name"] = company_name
        price_change = float(cur_price) / track["track_price"] - 1
        tracks_dict["price_change"] = str(round(price_change * 100, 2))+"%"
        if tracks_dict["buy_or_sell"] == 1:
            tracks_dict["buy_or_sell"] = "BUY"
        else:
            tracks_dict["buy_or_sell"] = "SELL"
            
        # update stock historical data
        track_list.append(tracks_dict)
    return track_list
