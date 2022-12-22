import sqlite3
import psycopg2
import defines as d

"""Ручная работа с базой данных, когда необходимо добавить таблицу/колонку без пересоздания. 
Самая полезная функция PARAM_PARSE - позволяет перенести новые предметы из файла items.txt в базу данных"""

# connect = sqlite3.connect('BotStalker.db')
connect = psycopg2.connect(dbname=d.DATABASE_INFO["dbname"], user=d.DATABASE_INFO["user"],
                        password=d.DATABASE_INFO["password"], host=d.DATABASE_INFO["host"])
cursor = connect.cursor()

cutsom_remove = True
#
# UPDATE users set left_hand = 0, right_hand = 0, active_artefact = 0, active_armor = 0, helmet = 0
#
if cutsom_remove:
    cursor.execute("""CREATE TABLE IF NOT EXISTS game_data(
        item_id INTEGER PRIMARY KEY,
        last_donut INTEGER
    )
    """)
    connect.commit()
    cursor.execute("INSERT INTO game_data (item_id, last_donut) values (1, 0)")
    connect.commit()
    exit(1)

# Обновление информации о предметах и боссах из файла items.txt без сноса базы данных
param_parse = False
# ///////////////////

# Переименовывание кучи однотипных строк
remove_items = False
base_name = 'NS_item'
remove_column_name = 'items'
start_del = 1
end_del = 40
start_add = 100
new_name = 'item'
# ///////////////////

# Обновление pid предмета, на случай если он был удален или перенесён
run_change_proto = False
new_value = 1
type_proto = 1
old_value = 16
# //////////////////

# Сброс всех групп игроков для боёв с боссами
resetGroups = False
# //////////////////

# Добавить новую колонку в таблицу
add_new_column = False
table_name = 'users'
column_name = 'img'
# column_name = 'backgrounds'
column_type = 'TEXT'  # 'INTEGER' 'TEXT'
column_value = 'n'
# prev_column_name = 'premium' # НЕ РАБОТАЕТ, столбец всегда добавляется в конец таблицы
# //////////////////

# Добавить новую таблицу
add_new_table = False
if add_new_table:
    cursor.execute("""CREATE TABLE IF NOT EXISTS skins(
        skin_id INTEGER PRIMARY KEY,
         name TEXT,
         source TEXT,
         filename TEXT
    )
    """)
# //////////////////


def add_column():
    cursor.execute(f'ALTER TABLE {table_name} ADD column {column_name} {column_type}')
    result = f"UPDATE {table_name} SET {column_name} = ?"
    data = [column_value]
    cursor.execute(result, data)


def reset_groups():
    cursor.execute(f'UPDATE users SET group_id = 0')
    cursor.execute(f'DELETE FROM groups')


def PARAM_PARSE(name):
    for k in range(len(name)):
        f = open('items.txt')
        while True:
            line = f.readline()
            if line[3:len(name[k]) + 3] == name[k]:
                break
            if not line:
                break
        while True:
            line = f.readline().split()
            if not line:
                break
            if line[0] == "//":
                break
            param_data = [
                line[j] for j in range(len(line))
            ]
            result = f'insert into {name[k]} values ('
            for j in range(len(line)):
                if not line[j].isdigit():
                    result += f'\'{line[j]}\','
                    continue
                result += line[j] + ','
            result = result[:-1]
            result += ')'
            cursor.execute(result)


def REMOVE_ITEMS():
    for ii in range(start_del, end_del+1):
        cursor.execute(f'ALTER TABLE {remove_column_name} RENAME COLUMN {base_name}{ii} TO {new_name}{start_add+ii}')


if param_parse:
    for i in d.DB_TABLE_NAMES:
        cursor.execute(f'DELETE FROM {i}')
    connect.commit()
    PARAM_PARSE(d.DB_TABLE_NAMES)

if run_change_proto:
    cursor.execute(f'UPDATE items_param SET proto_id = {new_value} WHERE type = {type_proto} AND proto_id = {old_value}')

if resetGroups:
    reset_groups()

if add_new_column:
    add_column()

if remove_items:
    REMOVE_ITEMS()

connect.commit()
