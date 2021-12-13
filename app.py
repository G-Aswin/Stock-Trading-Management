from flask import Flask, render_template, redirect, request
app = Flask(__name__)
from psycopg2 import connect


db_uri = "postgres://rgoiqssclvlyow:fdab72146a11bcff18e603f4f63a757f8f0d7777adf364cd8d1f3cbe0f972824@ec2-3-217-216-13.compute-1.amazonaws.com:5432/d822skk2e33c93"


@app.route('/')
def index():
    return render_template('index.html')




if __name__ == '__main__':
    app.run(debug=True)