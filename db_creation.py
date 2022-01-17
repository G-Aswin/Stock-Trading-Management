from psycopg2 import connect

URI = "postgres://fpuzyjbfomdapy:4366c003257264a984008affe1f706df034418bb08a8b95aeb96e5947d507d6f@ec2-34-205-209-14.compute-1.amazonaws.com:5432/db3gkh6jqmtthb"


# DATABASE_URL = os.environ.get(URI)
con = connect(URI)
cur = con.cursor()

# cur.execute('''  SELECT *
# FROM pg_catalog.pg_tables
# WHERE schemaname != 'pg_catalog' AND 
#     schemaname != 'information_schema';
#  ''')

# print(cur.fetchall())

# cur.execute(''' drop table portfolio; ''')
# cur.execute(''' drop table stock_transactions; ''')
# cur.execute(''' drop table bank_transaction; ''')
# cur.execute(''' drop table user_data; ''')
# cur.execute(''' drop table users; ''')


# cur.execute(''' create table users
#                 (
#                     unique_id serial primary key,
#                     username varchar(50) UNIQUE,
#                     password_hash varchar 
#                 ); ''')





# cur.execute(''' create table user_data
#                 (
#                     name varchar(30),
#                     phone_No varchar(10),
#                     email_id varchar(30),
#                     dob date,
#                     bank_acc_no int,
#                     age int,
#                     total_cash real,
#                     unique_id int references users(unique_id) ON DELETE CASCADE
#                 ); ''')

# cur.execute(''' create table bank_transaction
#                 (
#                     bank_transaction_id int,
#                     bank_name varchar(20),
#                     amount real,
#                     d_or_w char,
#                     tstamp timestamp,
#                     unique_id int references users(unique_id),
#                     primary key (bank_transaction_id)
#                 );''')


# cur.execute(''' create table stock_transactions
#                 (
#                     transaction_id serial,
#                     cost real,
#                     tstamp timestamp with time zone,
#                     symbol varchar(20),
#                     units int,
#                     unique_id int references users(unique_id),
#                     primary key (transaction_id)
#                 );''')


# cur.execute(''' create table portfolio
#                 (
#                     stock_name varchar,
#                     stock_symbol varchar(20),
#                     units_holding int,
#                     average_price real,
#                     unique_id int references users(unique_id),
#                     primary key (stock_symbol)
#                 );  ''')

# cur.execute("insert into users(username, password_hash) values('admin', '1234')")

cur.execute('''CREATE OR REPLACE FUNCTION update_total_cash(offset real, user int)
  RETURNS TRIGGER 
  LANGUAGE PLPGSQL
  AS
$$
BEGIN
    UPDATE user_data SET total_cash = total_cash - offset where unique_id = user
	RETURN NEW;
END;
$$''')



con.commit()
con.close()
