from flask import Flask, render_template, redirect, request, session
from psycopg2 import connect

from flask_session import Session
from tempfile import mkdtemp

import os
import datetime

from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required, lookup, usd

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

app.secret_key = b'aswin_g'


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
session = Session(app)



db_uri = "postgres://fpuzyjbfomdapy:4366c003257264a984008affe1f706df034418bb08a8b95aeb96e5947d507d6f@ec2-34-205-209-14.compute-1.amazonaws.com:5432/db3gkh6jqmtthb"
db = connect(db_uri)
db = db.cursor()

if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

@app.route('/')
@login_required
def index():
    # get user cash total
    # result = db.execute("SELECT cash FROM users WHERE id=:id", id=session["user_id"])
    db.execute("select total_cash from user_data where unique_id = %s", (session["unique_id"],))
    cash = 0
    for record in db:
        cash = record[0]

    # pull all transactions belonging to user
    db.execute("SELECT stock_symbol, units_holding FROM portfolio")
    portfolio = []
    for record in db:
        stock = {}
        stock.update({'stock':record[0], 'quantity':record[1]})
        portfolio.append(stock)
        

    if not portfolio:
        return apology("sorry you have no holdings")

    grand_total = cash

    # determine current price, stock total value and grand total value
    for stock in portfolio:
        price = lookup(stock['stock'])['price']
        total = stock['quantity'] * price
        stock.update({'price': price, 'total': total})
        grand_total += total

    return render_template("index.html", stocks=portfolio, cash=cash, total=grand_total)

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock."""

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure stock symbol and number of shares was submitted
        if (not request.form.get("stock")) or (not request.form.get("shares")):
            return apology("must provide stock symbol and number of shares")

        # ensure number of shares is valid
        if int(request.form.get("shares")) <= 0:
            return apology("must provide valid number of shares (integer)")

        # pull quote from yahoo finance
        quote = lookup(request.form.get("stock"))

        # check is valid stock name provided
        if quote == None:
            return apology("Stock symbol not valid, please try again")

        # calculate cost of transaction
        cost = int(request.form.get("shares")) * quote['price']

        # check if user has enough cash for transaction
        result = db.execute("SELECT cash FROM users WHERE id=:id", id=session["user_id"])
        if cost > result[0]["cash"]:
            return apology("you do not have enough cash for this transaction")

        # update cash amount in users database
        db.execute("UPDATE users SET cash=cash-:cost WHERE id=:id", cost=cost, id=session["user_id"]);

        # add transaction to transaction database
        add_transaction = db.execute("INSERT INTO transactions (user_id, stock, quantity, price, date) VALUES (:user_id, :stock, :quantity, :price, :date)",
            user_id=session["user_id"], stock=quote["symbol"], quantity=int(request.form.get("shares")), price=quote['price'], date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        # pull number of shares of symbol in portfolio
        curr_portfolio = db.execute("SELECT quantity FROM portfolio WHERE stock=:stock", stock=quote["symbol"])

        # add to portfolio database
        # if symbol is new, add to portfolio
        if not curr_portfolio:
            db.execute("INSERT INTO portfolio (stock, quantity) VALUES (:stock, :quantity)",
                stock=quote["symbol"], quantity=int(request.form.get("shares")))

        # if symbol is already in portfolio, update quantity of shares and total
        else:
            db.execute("UPDATE portfolio SET quantity=quantity+:quantity WHERE stock=:stock",
                quantity=int(request.form.get("shares")), stock=quote["symbol"]);

        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
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
        db.execute("SELECT unique_id FROM users WHERE username = %s", (request.form.get("username"),))
        rec_count = 0
        for record in db:
            print(record)
            session["unique_id"] = record[0]
            print("printing one record")
            rec_count += 1
        
        
        # Ensure username exists and password is correct
        if rec_count != 1 or not check_password_hash(rows[0]["password_hash"], request.form.get("password")):
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
    """Get stock quote."""

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure name of stock was submitted
        if not request.form.get("stock"):
            return apology("must provide stock symbol")

        # pull quote from yahoo finance
        quote = lookup(request.form.get("stock"))

        # check is valid stock name provided
        if quote == None:
            return apology("Stock symbol not valid, please try again")

        # stock name is valid
        else:
            return render_template("quoted.html", quote=quote)

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user."""

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password and password confirmation were submitted
        elif not request.form.get("password") or not request.form.get("password_confirm"):
            return apology("must provide password")

        # ensure password and password confirmation match
        elif request.form.get("password") != request.form.get("password_confirm"):
            return apology("password and password confirmation must match")

        # hash password
        hashval = generate_password_hash(request.form.get("password"))

        # add user to database
        db.execute("select unique_id from users where username = %s", (request.form.get("username"),))

        rec_count = 0
        for record in db:
            print(record)
            session["unique_id"] = record[0]
            rec_count += 1
        # ensure username is unique
        if rec_count != 0:
            return apology("username is already registered")
        
        name = request.form.get("name")
        phone_no = request.form.get("phone_no")
        email_id = request.form.get("email_id")
        dob = request.form.get("dob")
        acc_no = request.form.get("acc_no")
        age = request.form.get("age")
        cash = 10000
        
        db.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (request.form.get("username"), hashval))
        session["user_id"] = request.form.get("username")
        
        db.execute("select unique_id from users where username = %s", (request.form.get("username"),))
        rec_count = 0
        for record in db:
            print(record)
            session["unique_id"] = record[0]
            rec_count += 1
        
        # remember which user has logged in

        db.execute("insert into user_data values (%s, %s, %s, %s, %s, %s, %s, %s)", (name, phone_no, email_id, dob, acc_no, age, cash, session["unique_id"]))
        # redirect user to home page
        return redirect("/")

    # else if user reached route via GET (as by clicking a link or via redirect)
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