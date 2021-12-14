from flask import Flask, render_template, redirect, request
from psycopg2 import connect

from flask_session import Session
from tempfile import mkdtemp

import os
import datetime

from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
db_uri = "postgres://rgoiqssclvlyow:fdab72146a11bcff18e603f4f63a757f8f0d7777adf364cd8d1f3cbe0f972824@ec2-3-217-216-13.compute-1.amazonaws.com:5432/d822skk2e33c93"

if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

@app.route('/')
def index():
    @app.route("/")
@login_required
def index():
    portfolios = db.execute("SELECT * from portfolio where uniquej_id = ?", session["user_id"])

    list_of_stocks = []
    for portfolio in portfolios:
        if portfolio["stock"] not in list_of_stocks:
            list_of_stocks.append(portfolio["stock"])

    stock_data = {}

    for stock in list_of_stocks:
        stock_data[stock] = lookup(stock)

    total_money = 0
    for portfolio in portfolios:
        total_money += stock_data[portfolio['stock']]['price']*portfolio['stock_count']
        
    balance = 0
    bal = db.execute("SELECT cash from users where id = ?", session["user_id"])
    balance = float(bal[0]["cash"])
    balance = "{:.2f}".format(balance)

    return render_template("index.html", portfolios=portfolios, stock_data=stock_data, total_money=total_money, balance = balance, fb = float(balance))

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")
        symbol = symbol.upper()

        if not symbol:
            return apology("must provide symbol", 403)

        data_recieved = lookup(symbol)
        
        if not data_recieved:
            return apology("Invalid Symbol", 400)

        try:
            shares = float(shares)
        except ValueError:
            return apology("Not a valid integer", 400)
            
        if (int(shares) != shares) or (shares <= 0):
            return apology("Invalid shares", 400)
            
        latest_price = float(data_recieved["price"])

        money = db.execute("select cash, username from users where id = ?", session["user_id"])
        name = db.execute("select username from users where id = ?", session["user_id"])
        name = name[0]["username"]
        money = money[0]["cash"]

        money = float(money)
        
        
        user_id = session["user_id"]

        if data_recieved == None:
            return apology("Invalid symbol")
        if shares < 0:
            return apology("shares should be a whole number", 400)

        print(type(shares), type(latest_price))
        total_cost = shares * latest_price

        if money < total_cost:
            return apology("Your account doesn't have required balance to buy this stock")

        else:
            currentDateTime = datetime.datetime.now()
            
            stockexists = db.execute("select * from purchase where stock = ?", symbol)
            print(stockexists)
            if len(stockexists) == 0:
                print("inserting new")
                inserting = db.execute("insert into purchase(user_id, name, stock, price, time, stock_count) VALUES (?, ?, ?, ?, ?, ?)", user_id, name, symbol, total_cost, currentDateTime, shares)
            else:
                updatingold = db.execute("UPDATE purchase set stock_count = stock_count + ? where user_id = ?", shares, user_id)

            updating = db.execute("UPDATE users set cash = cash - ? where id = ?", total_cost, user_id)
            insert_history = db.execute("insert into history(id, Symbol, Shares, Price, Transacted) VALUES (?, ?, ?, ?, ?)", user_id, symbol, shares, latest_price, currentDateTime)
        return redirect("/")

    else:
        return render_template("buy.html")

@app.route("/history")
@login_required
def history():
    user_id = session["user_id"]
    portfolios = db.execute("SELECT Symbol, Shares, Price, Transacted from history where id = ?", session["user_id"])
    
    return render_template("history.html", portfolios=portfolios)
    return apology("TODO")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password_hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method == "POST":
        symbol = request.form.get("symbol")

        data_recieved = lookup(symbol)
        if data_recieved == None:
            return apology("Invalid symbol")
        if symbol.upper() == data_recieved["symbol"]:
            round_price = round(data_recieved["price"], 2)
            return render_template("quoted.html", data=data_recieved)

        else:
            return apology("Invalid symbol")
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
      # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        username = request.form.get("username")
        # while True:
        password = request.form.get("password")

        #if username is not provided
        if not username:
            return apology("must provide username", 400)
        #if username already present in the database
        used_usernames = []
        usernames = db.execute("select username from users")
        
        for entry in usernames:
            used_usernames.append(entry["username"])
        
        if username in used_usernames:
            return apology("this username already exist", 400)
        if not password:
            return apology("must provide password", 400)
        if not request.form.get("confirmation"):
            return apology("you must confirm the password")

        if password == request.form.get("confirmation"):
            hash_password = generate_password_hash(password)

        #inserting the username, hashed password in the database
            rows = db.execute("INSERT INTO users (username, password_hash) VALUES(?, ?)", username, hash_password)
        else:
            return apology("Password doesn't match, type again")
        return redirect("/")
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    stocks = db.execute("SELECT distinct(stock) from purchase where user_id = ?", session["user_id"])

    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")
        shares = int(shares)

        print("Recieved symbol : ", symbol)
        print("Recieved shares : ", shares)

        no_of_shares = db.execute("SELECT sum(stock_count) from purchase where user_id = ? and stock = ?", session["user_id"], symbol)
        no_of_shares = no_of_shares[0]['sum(stock_count)']
        print(no_of_shares)

        data_recieved = lookup(symbol)
        # store the price information of the required stock
        latest_price = data_recieved["price"]
        latest_price = float(latest_price)

        if not symbol:
            return apology("must provide symbol", 403)
        if shares > no_of_shares:
            return apology("The user does not own that many shares of the stock")
        
        updating = db.execute("UPDATE users set cash = cash + ? where id = ?", shares * latest_price, session["user_id"])
        shareupdate = db.execute("UPDATE purchase set stock_count = stock_count - ? where user_id = ?", shares, session["user_id"])
        currentDateTime = datetime.datetime.now()

        insert_history = db.execute("insert into history(id, Symbol, Shares, Price, Transacted) VALUES (?, ?, ?, ?, ?)", 
                                    session["user_id"], symbol, shares, latest_price, currentDateTime)
        return redirect("/")
    return render_template("sell.html", stocks=stocks)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

if __name__ == '__main__':
    app.run(debug=True)