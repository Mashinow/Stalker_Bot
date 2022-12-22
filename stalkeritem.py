import defines as d


def get_bin_param(param):
    return 2 ** (param - 1)


class Item:
    def __init__(self, ident, cursor):
        if __name__ == '__main__':
            base_names = []
            # cursor.execute('PRAGMA table_info(items_param);')
            cursor.execute(f'''SELECT
                column_name,
                ordinal_position
            FROM
                information_schema.columns
            WHERE
                table_name = 'items_param';''')
            data = d.quicksort(cursor.fetchall())
            for i in data:
                base_names.append(i[0])
        else:
            base_names = d.PRAGMA_ALL[0]
        cursor.execute(f'SELECT * FROM items_param WHERE id = {ident}')
        data = cursor.fetchall()
        data = data[0]
        for i in range(len(data)):
            setattr(self, base_names[i], data[i])
        if __name__ == '__main__':
            base_names = []
            # cursor.execute(f'PRAGMA table_info({d.ALL_TYPE_NAMES[self.type]});')
            cursor.execute(f'''SELECT
                column_name
            FROM
                information_schema.columns
            WHERE
                table_name = '{d.ALL_TYPE_NAMES[self.type]}';''')
            data = cursor.fetchall()
            for i in data:
                base_names.append(i[0])
        else:
            base_names = d.PRAGMA_ALL[self.type]
        cursor.execute(f'SELECT * FROM {d.ALL_TYPE_NAMES[self.type]} WHERE item_id = {self.proto_id}')
        data = cursor.fetchall()[0]
        for i in range(len(data)):
            setattr(self, base_names[i], data[i])
        self.name = self.name.replace('_', ' ')
        if not self.filename:
            self.filename = 'n'
        if not self.source:
            self.source = 'n'
        if self.is_have_mods():
            for i in self.get_all_mods():
                self.append_mode_params(self.get_all_mode_params(i, cursor))

    def append_mode_params(self, mode):  # не рефакторить, активные моды вообще не предметы
        names = d.PRAGMA_ALL[self.type][d.START_CHANGED_PARAMETERS:d.SOURCE_NUMBER]
        mode = mode[d.START_CHANGED_PARAMETERS:d.SOURCE_NUMBER]
        for i in range(len(names)):
            setattr(self, names[i], getattr(self, names[i])+int(mode[i]))

    def get_all_mode_params(self, proto_id, cursor):
        item_type = d.ITEM_ASSOCIATIONS[self.type]
        cursor.execute(f"SELECT * from {d.ALL_TYPE_NAMES[item_type]} WHERE item_id = {proto_id}")
        return cursor.fetchall()[0]

    def get_mode_name(self, proto_id, cursor):
        item_type = d.ITEM_ASSOCIATIONS[self.type]
        cursor.execute(f"SELECT name from {d.ALL_TYPE_NAMES[item_type]} WHERE item_id = {proto_id}")
        return cursor.fetchall()[0][0].replace('_', ' ')

    def add_mode_to_item(self, mod, cursor):
        self.update_param('mods', self.mods | get_bin_param(mod), cursor)
        self.append_mode_params(self.get_all_mode_params(mod, cursor))

    def is_mode_busy(self, proto_id):
        return self.mods & get_bin_param(proto_id)

    def is_rare(self):
        if self.is_stackable() and self.proto_id > d.BONUS_INTO_ID / 2:
            return True
        elif not self.is_stackable() and self.proto_id > d.START_RARE_ITEMS_PROTO:
            return True

    def is_stackable(self):
        if self.type in d.STACKABLE_TYPE:
            return True

    def is_weapon(self):
        if self.type == d.TYPE_WEAPONS_ID:
            return True

    def is_armor(self):
        if self.type == d.TYPE_ARMOR_ID:
            return True

    def is_artefact(self):
        if self.type == d.TYPE_ARTEFACTS_ID:
            return True

    def is_helmet(self):
        if self.type == d.TYPE_HELMETS_ID:
            return True

    def is_loot_case(self):
        if self.type == d.TYPE_LOOT_CASES_ID:
            return True

    def is_upgrades(self):
        if self.type in d.UPGRADE_TYPES:
            return True

    def is_upgrade_armor(self):
        if self.type == d.TYPE_UPGRADES_ARMOR_ID:
            return True

    def is_upgrade_weapon(self):
        if self.type == d.TYPE_UPGRADES_WEAPON_ID:
            return True

    def is_upgrade_helmet(self):
        if self.type == d.TYPE_UPGRADES_HELMET_ID:
            return True

    def is_have_mods(self):
        if self.type in d.ITEMS_CAN_HAVE_MODS:
            return True

    def is_can_broken(self):
        if self.type in [d.TYPE_WEAPONS_ID, d.TYPE_ARMOR_ID, d.TYPE_HELMETS_ID]:
            return True

    def is_can_use(self):
        if self.type == d.TYPE_USE_ITEMS:
            return True

    def is_broken(self):
        if self.iznos <= 0:
            return True

    def is_clothes(self):
        if self.type in d.ITEMS_CAN_PUT:
            return True

    def get_price(self):
        return int(self.price // d.ITEMS_SALE_PENALTY)

    def get_emoji_name(self):
        return f'{d.ALL_TYPE_EMOJI[self.type]} {self.name}'

    def get_all_proto_params(self):
        res = []
        for i in d.PRAGMA_ALL[self.type]:
            res.append(getattr(self, i))
        return res

    def get_all_mods(self):
        res = []
        for i in range(1, 33):
            if self.mods & get_bin_param(i):
                res.append(i)
        return res

    def draw_params(self, cursor):
        res = ''
        names = d.PRAGMA_ALL[self.type][1:-2]
        params = d.ALL_ITEM_SIGNATURES[self.type]
        for i in range(len(names)):
            try:
                if getattr(self, names[i]):
                    res += f'{params[i]}: {getattr(self,names[i])}\n'
            except IndexError:
                print(res)
        res += f'🤝 Цена продажи: {self.get_price()}\n'
        if self.is_can_broken():  # на данный момент не используется, задел на будущее
            res += f'🔧 Прочность: {self.iznos}\n'
        if self.is_have_mods():
            mods = self.get_all_mods()
            for i in range(len(mods)):
                res += f'⚙ Мод {i+1}: {self.get_mode_name(mods[i], cursor)}\n'

        return res.replace('_', ' ')

    def update_param(self, name, value, cursor):
        setattr(self, name, value)
        cursor.execute(f"UPDATE {d.ALL_TYPE_NAMES[0]} SET {name} = {value} WHERE id = {self.id}")

    def update_count(self, bonus, cursor):
        self.update_param('count', self.count + bonus, cursor)
        if self.count <= 0:
            print('UPDATE_COUNT_ERROR')

    def get_mode_type(self):
        return d.ITEM_ASSOCIATIONS[self.type]


def start():
    import sqlite3
    connect = sqlite3.connect('BotStalker.db', check_same_thread=False)
    cursor = connect.cursor()
    for i in range(len(d.ALL_TYPE_NAMES)):
        cursor.execute(f'PRAGMA table_info({d.ALL_TYPE_NAMES[i]});')
        data = cursor.fetchall()
        for j in data:
            d.PRAGMA_ALL[i].append(j[1])
    test = Item(51, cursor)
    print(test.draw_params(cursor))


if __name__ == '__main__':
    start()
