-- Initialize the database.
-- Drop any existing data and create empty tables.
DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS stock;
DROP TABLE IF EXISTS track;
DROP TABLE IF EXISTS SPY;
DROP TABLE IF EXISTS hist_price;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT, 
  username TEXT UNIQUE NOT NULL, 
  password TEXT NOT NULL, -- user password
  balance NUMERIC NOT NULL,
  is_admin INTEGER NOT NULL --current balance of the user, initialize wth $1,000,000
);

--a table for user and stock, save each stock with its user id and shares, to chow user account information
CREATE TABLE stock (
  stock_id INTEGER PRIMARY KEY AUTOINCREMENT, 
  author_id INTEGER NOT NULL, --reference user id
  stock_symbol TEXT NOT NULL,
  stock_name TEXT NOT NULL,
  total_shares INTEGER NOT NULL, --num of shares the author has totally
  FOREIGN KEY (author_id) REFERENCES user (id)
);

--a table for user and track, track each buy/sell by one user
CREATE TABLE track (
  author_id INTEGER NOT NULL, --reference user id
  track_id INTEGER PRIMARY KEY AUTOINCREMENT,
  stock_symbol TEXT NOT NULL,
  stock_name TEXT NOT NULL,
  date_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, --the time of buy/sell
  track_price NUMERIC NOT NULL, --the price the user buy/sell
  num_share INTEGER NOT NULL, --num of shares the author buy/sell
  buy_or_sell INTEGER NOT NULL, --buy: 1 sell: 0
  FOREIGN KEY (author_id) REFERENCES user (id)
);

-- a table to collect SPY index
CREATE TABLE SPY (
  track_id INTEGER PRIMARY KEY AUTOINCREMENT,
  date_time TIMESTAMP NOT NULL,
  index_value NUMERIC NOT NULL
);

-- a table to collect historical stock data
CREATE TABLE hist_price (
  track_id INTEGER PRIMARY KEY AUTOINCREMENT,
  stock_symbol TEXT NOT NULL,
  date_time TIMESTAMP NOT NULL,
  stock_price NUMERIC NOT NULL,
  FOREIGN KEY (stock_symbol) REFERENCES stock(stock_symbol)
);
