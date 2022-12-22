import defines as d


is_sqlite = False

if is_sqlite:
    import sqlite3
    connect = sqlite3.connect('BotStalker.db')
else:
    import psycopg2
    connect = psycopg2.connect(dbname=d.DATABASE_INFO["dbname"], user=d.DATABASE_INFO["user"],
                        password=d.DATABASE_INFO["password"], host=d.DATABASE_INFO["host"])
cursor = connect.cursor()

"""
Первичная генерация базы данных. Раньше работала с sqlite3, сейчас проект его не поддерживает, 
лучше генерировать psycopg2. Этот файл запускается первым при отсутствии базы данных в проекте
"""

if not is_sqlite:
    cursor.execute('''DROP SCHEMA public CASCADE;
    CREATE SCHEMA public;
    GRANT ALL ON SCHEMA public TO postgres;
    GRANT ALL ON SCHEMA public TO public;
    COMMENT ON SCHEMA public IS 'standard public schema';''')
    connect.commit()


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
            # param_data = [
            #     line[j] for j in range(len(line))
            # ]
            # for k2 in range(len(param_data)):
            #     if not param_data[k2].isdigit():
            #         param_data[k2] = f'\'{param_data[k2]}\''
            result = f'insert into {name[k]} values ('
            for j in range(len(line)):
                if not line[j].isdigit():
                    result += f'\'{line[j]}\','
                    continue
                result += line[j] + ','
            result = result[:-1]
            result += ')'
            cursor.execute(result)
            # result = "insert into " + name[k] + " values (" + "?," * (len(line) - 1) + "?)"
            # cursor.execute(result, param_data)


# Пользователь
cursor.execute("""CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    user_name TEXT,
    background INTEGER,
    premium INTEGER,
    location INTEGER,
    balance INTEGER,
    lvl INTEGER,
    opit INTEGER,
    energy INTEGER,
    rating INTEGER,
    damage INTEGER,
    armor INTEGER,
    emp INTEGER,
    punch INTEGER,
    razriv INTEGER,
    radiation INTEGER,
    chemical_burn INTEGER,
    blast INTEGER,
    shot INTEGER,
    regen INTEGER,
    current_hp INTEGER,
    max_hp INTEGER,
    dollars INTEGER,
    left_hand INTEGER,
    right_hand INTEGER,
    active_artefact INTEGER,
    active_armor INTEGER,
    helmet INTEGER,
    crit_chance INTEGER,
    bar INTEGER,
    skin INTEGER,
    chance_to_hit INTEGER,
    damage_type INTEGER,
    dodge INTEGER,
    items_rating INTEGER,
    group_id INTEGER,
    last_peer_id INTEGER,
    is_ban INTEGER,
    penetrate INTEGER,
    events INTEGER,
    skins INTEGER,
    backgrounds INTEGER,
    ref_src TEXT,
    img TEXT
)
""")

# Массив с предметами каждого игрока
cursor.execute("""CREATE TABLE IF NOT EXISTS items(
    user_id INTEGER PRIMARY KEY
)
""")
# if first_generate == 1:
for i in range(1, d.MAX_ITEMS + 1):
    data = "ALTER TABLE items ADD COLUMN item" + str(i) + " INTEGER"
    cursor.execute(data)
# for i in range(1, d.MAX_ITEMS_ST + 1):
#     data = "ALTER TABLE items ADD COLUMN NS_item" + str(i) + " INTEGER"
#     cursor.execute(data)

# Статистика игроков
cursor.execute("""CREATE TABLE IF NOT EXISTS stat(
    user_id INTEGER PRIMARY KEY,
    day_in_game INTEGER,
    wins INTEGER,
    looses INTEGER
)
""")
# if first_generate == 1:
for i in range(1, d.BOSS_COUNT + 1):
    data = "ALTER TABLE stat ADD COLUMN bosses" + str(i) + " INTEGER"
    cursor.execute(data)

# Массив всех предметов с уникальными идентификаторами и свойствами
cursor.execute("""CREATE TABLE IF NOT EXISTS items_param(
    id INTEGER PRIMARY KEY,
    proto_id INTEGER,
    type INTEGER,
    iznos INTEGER,
    mods INTEGER,
    flags INTEGER,
    count INTEGER,
    owner_id INTEGER
)
""")
# # if first_generate == 1:
# for i in range(1, d.MAX_MODS_COUNT + 1):
#     data = "ALTER TABLE items_param ADD COLUMN mods" + str(i) + " INTEGER"
#     cursor.execute(data)

# Все игровые локации
cursor.execute("""CREATE TABLE IF NOT EXISTS locations(
    locations_id INTEGER PRIMARY KEY,
     name TEXT,
     source TEXT,
     filename TEXT
)
""")

# Все фоны картинки с игроком
cursor.execute("""CREATE TABLE IF NOT EXISTS background(
    background_id INTEGER PRIMARY KEY,
     name TEXT,
     source TEXT,
     filename TEXT
)
""")

# Игровые боссы и их параметры
cursor.execute("""CREATE TABLE IF NOT EXISTS bosses(
    user_id INTEGER PRIMARY KEY,
    user_name TEXT,
    damage_type INTEGER,
    damage INTEGER,
    crit_chance INTEGER,
    chance_to_hit INTEGER,
    armor INTEGER,
    emp INTEGER,
    punch INTEGER,
    razriv INTEGER,
    radiation INTEGER,
    chemical_burn INTEGER,
    blast INTEGER,
    shot INTEGER,
    regen INTEGER,
    max_hp INTEGER,
    dodge INTEGER,
    penetrate INTEGER,
    source TEXT,
    filename TEXT
)
""")

# Типы предметов
cursor.execute("""CREATE TABLE IF NOT EXISTS item_type(
    item_id INTEGER PRIMARY KEY,
     name TEXT,
     table_name TEXT
)
""")

# Скины
cursor.execute("""CREATE TABLE IF NOT EXISTS skins(
    skin_id INTEGER PRIMARY KEY,
     name TEXT,
     source TEXT,
     filename TEXT
)
""")

string_armors = """(
    item_id INTEGER PRIMARY KEY,
     name TEXT,
     armor INTEGER,
     emp INTEGER,
     punch INTEGER,
     razriv INTEGER,
     radiation INTEGER,
     chemical_burn INTEGER,
     blast INTEGER,
     shot INTEGER,
     regen INTEGER,
     hp_up INTEGER,
     dodge INTEGER,
     price INTEGER,
     source TEXT,
     filename TEXT
)
"""
# Броня
cursor.execute('CREATE TABLE IF NOT EXISTS armors' + string_armors)

# Артефакты
cursor.execute('CREATE TABLE IF NOT EXISTS artefacts' + string_armors)

# Шлемы
cursor.execute('CREATE TABLE IF NOT EXISTS helmets' + string_armors)

# Модификация брони
cursor.execute('CREATE TABLE IF NOT EXISTS upgrades_armor' + string_armors)

# Модификация шлемов
cursor.execute('CREATE TABLE IF NOT EXISTS upgrades_helmet' + string_armors)

string_weapons = """(
    item_id INTEGER PRIMARY KEY,
     name TEXT,
     damage_type INTEGER,
     damage INTEGER,
     critical_chance INTEGER,
     chance_to_hit INTEGER,
     penetrate INTEGER,
     price INTEGER,
     source TEXT,
     filename TEXT
)
"""

# Оружие
cursor.execute('CREATE TABLE IF NOT EXISTS weapons' + string_weapons)

# Модификация оружия
cursor.execute('CREATE TABLE IF NOT EXISTS upgrades_weapon' + string_weapons)

# Лут-кейсы
cursor.execute("""CREATE TABLE IF NOT EXISTS loot_cases(
    item_id INTEGER PRIMARY KEY,
     name TEXT,
     price INTEGER,
     source TEXT,
     filename TEXT
)
""")

# особые игровые переменные
cursor.execute("""CREATE TABLE IF NOT EXISTS game_data(
    item_id INTEGER PRIMARY KEY,
    last_donut INTEGER
)
""")

# Используемые итемы
cursor.execute("""CREATE TABLE IF NOT EXISTS use_items(
    item_id INTEGER PRIMARY KEY,
    name TEXT,
    price INTEGER,
    source TEXT,
    filename TEXT
)
""")
# Лоты для аукциона
cursor.execute("""CREATE TABLE IF NOT EXISTS auction(
    item_id INTEGER PRIMARY KEY,
     name TEXT,
     owner_id INTEGER,
     price INTEGER
)
""")
# Группы игроков для боссов
cursor.execute("""CREATE TABLE IF NOT EXISTS groups(
    group_id INTEGER PRIMARY KEY,
     player1 INTEGER,
     player2 INTEGER,
     player3 INTEGER
)
""")
names = d.DB_TABLE_NAMES
PARAM_PARSE(names)

connect.commit()

cursor.execute("INSERT INTO game_data (item_id, last_donut) values (1, 0)")
connect.commit()

cursor.close()
