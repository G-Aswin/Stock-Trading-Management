from psycopg2 import connect

URI = "postgres://rgoiqssclvlyow:fdab72146a11bcff18e603f4f63a757f8f0d7777adf364cd8d1f3cbe0f972824@ec2-3-217-216-13.compute-1.amazonaws.com:5432/d822skk2e33c93"


# DATABASE_URL = os.environ.get(URI)
con = connect(URI)
cur = con.cursor()

# cur.execute('''  SELECT *
# FROM pg_catalog.pg_tables
# WHERE schemaname != 'pg_catalog' AND 
#     schemaname != 'information_schema';
#  ''')

# print(cur.fetchall())

cur.execute(''' drop table portfolio; ''')
cur.execute(''' drop table stock_transactions; ''')
cur.execute(''' drop table bank_transaction; ''')
cur.execute(''' drop table user_data; ''')
cur.execute(''' drop table users; ''')


cur.execute(''' create table users
                (
                    unique_id serial primary key,
                    username varchar(50) NOT NULL,
                    password_hash varchar UNIQUE
                ); ''')





cur.execute(''' create table user_data
                (
                    name varchar(30),
                    phone_No varchar(10),
                    email_id varchar(30),
                    dob date,
                    bank_acc_no int,
                    age int,
                    unique_id int references users(unique_id) ON DELETE CASCADE
                ); ''')

cur.execute(''' create table bank_transaction
                (
                    bank_transaction_id int,
                    bank_name varchar(20),
                    amount real,
                    d_or_w char,
                    tstamp timestamp,
                    unique_id int references users(unique_id),
                    primary key (bank_transaction_id)
                );''')


cur.execute(''' create table stock_transactions
                (
                    transaction_id int,
                    cost real,
                    tstamp timestamp,
                    symbol varchar(20),
                    units int,
                    unique_id int references users(unique_id),
                    primary key (transaction_id)
                );''')


cur.execute(''' create table portfolio
                (
                    stock_name varchar(20),
                    stock_symbol varchar(20),
                    units_holding int,
                    average_price real,
                    unique_id int references users(unique_id),
                    primary key (stock_symbol)
                );  ''')



con.commit()
con.close()
