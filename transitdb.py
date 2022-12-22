import sqlite3
import psycopg2
import defines as d

"""
Перенос базы данных из sql3 в psycorg2. Использовалось единожды при переезде на новую бд.
"""

lite_con = sqlite3.connect('BotStalker.db')
lite_cur = lite_con.cursor()
post_con = psycopg2.connect(dbname=d.DATABASE_INFO["dbname"], user=d.DATABASE_INFO["user"],
                            password=d.DATABASE_INFO["password"], host=d.DATABASE_INFO["host"])
post_cur = post_con.cursor()
post_cur.execute('''SELECT table_name FROM information_schema.tables
WHERE table_schema NOT IN ('information_schema','pg_catalog');''')
all_tables = post_cur.fetchall()
for row in all_tables:
    table_name = row[0]
    lite_cur.execute(f'SELECT * from {table_name}')
    data = lite_cur.fetchall()
    for rw in data:
        command = f'insert into {table_name} values ('
        for param in rw:
            if not str(param).isdigit():
                if param is None:
                    param = int(0)
                else:
                    param = f'\'{param}\''
            command += f'{param},'
        command = command[:-1]
        command += ') ON CONFLICT DO NOTHING'
        post_cur.execute(command)

post_con.commit()
