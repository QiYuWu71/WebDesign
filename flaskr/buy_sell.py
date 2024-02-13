from flask import flash
from flaskr.db import get_db
from flaskr.get_db_data import get_cur_user
from flaskr.get_data import get_cur_price, get_company_name
from flaskr.update_db import init_hist

def buy_sell_action(stock_symbol, num_share, buysell, g, error):
    new_balance = 0

    db = get_db()
    # get user name and balance, help to calculate changed balance to confirm buy/sell
    u_dict = get_cur_user(db, g)

    # get user stocks, help to calculate balance and update stock
    stock = db.execute(
        "SELECT stock_symbol, stock_name, total_shares"
        " FROM stock s JOIN user u ON s.author_id = u.id"
        " WHERE id = ? AND stock_symbol = ?", (g.user["id"], stock_symbol)
    ).fetchall()
    s_dict = {} # stock dict
    total_shares = 0
    # get a stock dict of the current user, the logic is same as above
    for s in stock:
        # sqlite3.Row to dict
        s_dict = dict(s)
        total_shares = s_dict["total_shares"]
    
    current_balance = u_dict["balance"] # current balance got from database
    # get current price at the time the user buy/sell
    track_price = get_cur_price(stock_symbol)

    # set buy_sell_flag value, change balance, add stock num of shares, add this into database
    if buysell.upper() == "BUY":
        buy_sell_flag = 1
        # if balance not enough, error
        if current_balance < num_share * track_price:
            error = "Insufficient balance."
        if error is not None:
            flash(error,'error')
        else:
            new_balance = round(current_balance - num_share * track_price,2)
            stock_name = get_company_name(stock_symbol)
            
            db = get_db()
            # if the buy stock not in database, insert the stock into database, else update the stock in database
            if total_shares == 0:
                total_shares = num_share
                db.execute(
                    "INSERT INTO stock (stock_symbol, stock_name, total_shares, author_id) VALUES (?, ?, ?, ?)",
                    (stock_symbol, stock_name, total_shares, g.user["id"]),
                )
                #3. update the bought stock's historical data in database if not within in the database, else keep it.
                whole_stock_list = db.execute(
                    "SELECT DISTINCT stock_symbol from stock"
                ).fetchall()

                if stock_symbol not in whole_stock_list:
                    init_hist(stock_symbol,db)
            else:
                total_shares += num_share
                db.execute(
                    "UPDATE stock SET total_shares = ? WHERE author_id = ? AND stock_symbol = ?",
                    (total_shares, g.user["id"], stock_symbol),
                )
            db.commit()
        
    if buysell.upper() == "SELL":
        buy_sell_flag = 0
        # if stock num of shares not enough, error
        if total_shares < num_share:
            error = "Insufficient shares of stock."
        if error is not None:
            flash(error)
        else:
            total_shares -= num_share
            new_balance = round(current_balance + num_share * track_price,2)
        
            db = get_db()
            # if sold out all the shares of stock, delete the stock in database, else update the num of shares in database
            if total_shares == 0:
                db.execute(
                    "DELETE FROM stock WHERE author_id = ? AND stock_symbol = ?",
                    (g.user["id"], stock_symbol),
                )
    # 3. check whether the symbol is used by other user, if not, delete the stock_symbol from the local database.
                # read the stock database to check whether there are multiple users select the stock

                counts = db.execute(
                    "SELECT count(*) from stock where stock_symbol = ?",
                    (stock_symbol,),
                ).fetchall()

                if counts == 0:  
                    db.execute(
                        "DELETE FROM hist_price WHERE stock_symbol = ?",
                        (stock_symbol,),
                    )
            else:
                db.execute(
                    "UPDATE stock SET total_shares = ? WHERE author_id = ? AND stock_symbol = ?",
                    (total_shares, g.user["id"], stock_symbol),
                )
            db.commit()
    
    return track_price, buy_sell_flag, new_balance, error