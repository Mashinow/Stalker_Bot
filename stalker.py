import time
import datetime
import defines as d
from PIL import Image, ImageDraw, ImageFont
import io
from random import choice
import os
# import sqlite3
from copy import deepcopy
import operator
from stalkergroup import Group
from stalkeritem import Item
from vk_api import exceptions
from requests import exceptions as Rexceptions
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from keksik import KeksikApi

"""
Здесь расположено основное тело программы: класс игрока, класс нпс, игровая боёвка и несколько потоковых функций
"""


def clamp(value, minv, maxv):
    return max(min(value, maxv), minv)


def get_random_anekdot():
    total_bytes = os.stat(d.DEFAULT_ANEKDOTS_PATH).st_size
    random_point = d.GAME_RANDOM.Random(0, total_bytes - 170)
    file = open(d.DEFAULT_ANEKDOTS_PATH)
    file.seek(random_point)
    res = ''
    while True:
        temp = file.readline()
        if temp != '\n':
            continue
        break
    while True:
        temp = file.readline()
        res += temp
        if temp != '\n':
            continue
        break
    return res


def get_database_item_param_from_name(base_name, param_name, string_id, cursor):
    result = f"SELECT {param_name} from {base_name} WHERE item_id = {string_id}"
    cursor.execute(result)
    for find in cursor:
        return find[0]


def get_bin_param(param):
    return 2 ** (param - 1)


def get_list_bin_params(param):
    res = []
    for i in range(1, 33):
        if param & get_bin_param(i):
            res.append(i)
    return res


def get_database_params_from_id(base_name, param_numbers, string_id, cursor):
    result = f"SELECT * from {base_name}"
    data = []
    cursor.execute(result)
    for find in cursor:
        if find[0] == string_id:
            for i in range(len(param_numbers)):
                data.append(find[param_numbers[i]])
            return data


def check_image_valid(path, second_path=""):
    path = f"{d.DEFAULT_IMAGE_PATH}{second_path}{path}{d.DEFAULT_IMAGE_FORMAT}"
    if not os.path.isfile(path):
        return Image.open(f"{d.DEFAULT_IMAGE_PATH}{d.DEFAULT_PICTURE_SOURCE}{d.DEFAULT_IMAGE_FORMAT}")
    else:
        art = Image.open(path)
        return art


def player_connect(player_id, cursor):
    if player_id in d.active_users:
        player = d.get_player(player_id)
    else:
        player = Stalker(player_id, cursor, False)
    return player


def get_fast_item_params(uid, cursor):  # не рефакторить, используется только для слотов
    if not uid:
        return 0
    temp = get_database_params_from_id('items_param', d.ITEMS_PARAM_FULL, uid, cursor)
    mods = get_list_bin_params(temp[d.ITEMS_PARAM_MODS])
    # for i in range(d.START_PARAM_MODS, d.END_PARAM_MODS):
    #     if temp[i]:
    #         mods.append(i - len(d.ITEMS_PARAM_ALL) + 1)
    result = f"SELECT * from {d.ALL_TYPE_NAMES[temp[d.ITEMS_PARAM_TYPE]]} WHERE item_id = {temp[d.ITEMS_PARAM_PROTO_ID]}"
    cursor.execute(result)
    for find in cursor:
        return [find, mods if mods else 0]


def append_mode_params(item, mode):  # не рефакторить, активные моды вообще не предметы
    item = list(item)
    for i in range(d.START_CHANGED_PARAMETERS, len(mode) + d.SOURCE_NUMBER):
        item[i] += mode[i]
    return item


# def get_stackable_item_name(cursor, data):
#     item_id = data[0] % d.BONUS_INTO_ID
#     item_type = d.STACKABLE_TYPE[data[0] // d.BONUS_INTO_ID]
#     params = [item_id]
#     result = f"SELECT * from {d.ALL_TYPE_NAMES[item_type]} WHERE item_id = ?"
#     for find in cursor.execute(result, params):
#         return find[1].replace('_', ' ')
#     return ''


def get_all_mode_params(cursor, item_type, proto_id):  # не рефакторить
    item_type = d.ITEM_ASSOCIATIONS[item_type]
    result = f"SELECT * from {d.ALL_TYPE_NAMES[item_type]} WHERE item_id = {proto_id}"
    cursor.execute(result)
    for find in cursor:
        return find


def get_mode_name(cursor, item_type, proto_id):  # не рефакторить
    item_type = d.ITEM_ASSOCIATIONS[item_type]
    result = f"SELECT * from {d.ALL_TYPE_NAMES[item_type]} WHERE item_id = {proto_id}"
    cursor.execute(result)
    for find in cursor:
        return find[1]


# def get_all_stackable_item_params(cursor, data):
#     item_id = data[0] % d.BONUS_INTO_ID
#     item_type = d.STACKABLE_TYPE[data[0] // d.BONUS_INTO_ID]
#     params = [item_id]
#     result = f"SELECT * from {d.ALL_TYPE_NAMES[item_type]} WHERE item_id = ?"
#     for find in cursor.execute(result, params):
#         return find


# def get_all_no_stack_item_params(base_name, item_id, cursor):
#     data = [item_id]
#     result = f"SELECT * from {base_name} WHERE item_id = ?"
#     for find in cursor.execute(result, data):
#         return find


# def get_item_name(cursor, uid):
#     if uid == 0:
#         return ''
#     temp = get_database_params_from_id('items_param', [d.ITEMS_PARAM_PROTO_ID, d.ITEMS_PARAM_TYPE], uid, cursor)
#     result = f"SELECT * from {d.ALL_TYPE_NAMES[temp[1]]} WHERE item_id = ?"
#     data = [temp[0]]
#     for find in cursor.execute(result, data):
#         res_str = str(find[1]).replace('_', ' ')
#         return res_str


def get_item_name_proto(cursor, pid, type):  # не рефакторить
    if pid == 0:
        return ''
    result = f"SELECT * from {d.ALL_TYPE_NAMES[type]} WHERE item_id = {pid}"
    cursor.execute(result)
    for find in cursor:
        res_str = str(find[1]).replace('_', ' ')
        return res_str


# def get_proto_params_from_uid(item_id, param_numbers, cursor):
#     temp = get_database_params_from_id('items_param', [d.ITEMS_PARAM_PROTO_ID, d.ITEMS_PARAM_TYPE], item_id, cursor)
#     return get_database_params_from_id(d.ALL_TYPE_NAMES[temp[1]], param_numbers, item_id, cursor)


def check_valid_player_id(_id, cursor):
    data = None
    cursor.execute(f"SELECT * from users WHERE user_id = {_id}")
    for row in cursor:
        data = row
        break
    if not data:
        return False
    return True


# def get_item_type(uid, cursor):
#     cursor.execute(f'SELECT type FROM items_param WHERE item_id = {uid}')
#     return int(cursor.fetchall()[0][0])


def check_flag(val, param):
    return val & get_bin_param(param)


class Stalker:

    def __init__(self, ident, cursor, first):
        current_time = time.time()
        self.peer_id = 0
        self.user_id = ident
        self.lastitem = 0  # номер последнего итема в инвентаре, не айди
        self.spam = current_time - 10  # защищает от общего спама сообщениями
        self.hard_spam = current_time - 60  # защищает от спама ресурсозатратных функций вроде отрисовки сталкера
        self.inventory_page = 0
        self.auction_page = 0
        self.last_stavka = 0
        self.selected_item = None  # объект последнего выбранного итема из инвентаря
        self.keyboard = 1  # активная клавиатурка
        self.temp_data = []  # 0 индекс - тип данных, остальное сами данные
        self.items = []
        self.items_obj = []  # рефакторинг
        self.skills = 0
        self.connect_time = current_time
        self.current_skill = 0
        self.side = 0  # 1 - лево, 2 - право
        self.target = None  # для боёвки
        self.is_player = True  # для боёвки
        self.is_busy = False  # для боёвки
        self.selected_boss = 0  # для атаки по боссу
        self.fight_ready = False  # для очереди на босса
        self.last_edit_message = 0  # для редактирования в процессе боёвки
        self.skills_cd = 0
        self.img_ready = False
        self.rating_lst = []
        self.buy_info = []  # для доната, запоминает номер товара для покупки за монетки
        if first:
            self.user_name = "Stalker" + str(1111 + d.Global_Item_Id)
            self.background = 0
            self.premium = 0
            self.location = 1
            self.balance = 500
            self.lvl = 1
            self.opit = 0
            self.energy = 50
            self.rating = 0
            self.damage = 0
            self.armor = 0
            self.emp = 0
            self.punch = 0
            self.razriv = 0
            self.radiation = 0
            self.chemical_burn = 0
            self.blast = 0
            self.shot = 0
            self.regen = 0
            self.max_hp = 0
            self.current_hp = 0
            self.dollars = 10
            self.left_hand = 0
            self.right_hand = 0
            self.active_artefact = 0
            self.active_armor = 0
            self.helmet = 0
            self.crit_chance = 0
            self.bar = 0
            self.skin = 0
            self.chance_to_hit = 0
            self.damage_type = 0
            self.dodge = 0
            self.items_rating = 0
            self.group_id = 0
            self.last_peer_id = 0
            self.is_ban = 0
            self.penetrate = 0
            self.events = 0x7fffffff  # ПРЕДЕЛ 2^31
            self.skins = 0  # ПРЕДЕЛ 2^31
            self.backgrounds = 0  # ПРЕДЕЛ 2^31
            self.ref_src = 'n'
            self.img = 'n'
            self.calculate_player_parameters(cursor)
            if self.user_id in d.ADMINISTRATORS:
                self.user_name = 'Admin'
                self.skin = 31
                self.lvl = 99
                self.max_hp = 9999
                self.current_hp = self.max_hp
                self.balance = 9999
                self.damage = 999
                self.armor = 999
                self.crit_chance = 100
                self.regen = 666
                self.dollars = 1000
                self.energy = 1000
                self.chance_to_hit = 999
                self.dodge = 999
                self.penetrate = 200
                self.add_bin_param(cursor, 31, d.BIN_TYPE_SKINS)
                self.skills = len(d.ALL_SKILLS)
            Stalker.data_init(self, cursor)
        else:
            Stalker.stat_parse(self, cursor)
            self.calculate_player_parameters(cursor)

        self.src_name = f'[id{self.user_id}|{self.user_name}]'
        if self.user_id in d.ADMINISTRATORS:
            self.src_name = f'[id1|Admin]'
        cursor.execute(f"insert into items(user_id) values ({self.user_id}) ON CONFLICT DO NOTHING")
        d.player_objects.append(self)
        self.get_inventory(first, cursor)
        d.active_users.append(self.user_id)

    def stat_parse(self, cursor):
        # data = [self.id]
        # cursor.execute("insert or ignore into users (user_id) values (?)", data)
        string = f"SELECT * from users WHERE user_id = {self.user_id}"
        cursor.execute(string)
        for row in cursor:
            if row[d.PLAYER_ID[0]] == self.user_id:
                for i in d.ALL_PLAYER_PARAMS:
                    setattr(self, i[1], row[i[0]])

            string = f"SELECT * from items WHERE user_id = {self.user_id}"
            cursor.execute(string)
            for row_2 in cursor:
                for i in range(d.START_PLAYER_ITEMS, d.END_PLAYER_ITEMS):
                    if row_2[i]:
                        self.lastitem = i
        # self.left_hand = Item(self.left_hand, cursor)
        # self.right_hand = Item(self.right_hand, cursor)
        # self.active_armor = Item(self.active_armor, cursor)
        # self.active_artefact = Item(self.active_artefact, cursor)
        # self.helmet = Item(self.helmet, cursor)

    def data_init(self, cursor):
        bd_data = [getattr(self, i) for i in d.ALL_PLAYER_PARAMS_NAMES]
        result = 'insert into users values ('
        for row in bd_data:
            if not str(row).isdigit():
                row = f'\'{row}\''
            result += f'{row},'
        result = result[:-1]
        result += ') ON CONFLICT DO NOTHING'
        cursor.execute(result)
        cursor.execute(f'insert into stat (user_id) values ({self.user_id}) ON CONFLICT DO NOTHING')

    def data_change(self, cursor):
        result = "UPDATE users SET "
        new_params = [getattr(self, i) for i in d.ALL_PLAYER_PARAMS_NAMES]
        for i in range(d.START_CHANGED_PARAMETERS, len(d.ALL_PLAYER_PARAMS_NAMES)):
            if type(new_params[i]) == str:
                continue
            buffer = str(d.ALL_PLAYER_PARAMS_NAMES[i]) + '=' + str(new_params[i]) + ", "
            result = result + buffer
        result = result[:-2]
        buffer = " WHERE user_id = " + str(
            self.user_id)
        result = result + buffer
        cursor.execute(result)

    def calculate_player_parameters(self, cursor):
        if self.user_id in d.ADMINISTRATORS:
            self.skills = len(d.ALL_SKILLS)
            self.img_ready = False
            return
        left_hand = get_fast_item_params(self.left_hand, cursor)
        right_hand = get_fast_item_params(self.right_hand, cursor)
        armor = get_fast_item_params(self.active_armor, cursor)
        artefact = get_fast_item_params(self.active_artefact, cursor)
        helmet = get_fast_item_params(self.helmet, cursor)
        all_active_items = [(left_hand, d.TYPE_WEAPONS_ID), (right_hand, d.TYPE_WEAPONS_ID),
                            (armor, d.TYPE_ARMOR_ID), (artefact, d.TYPE_ARTEFACTS_ID), (helmet, d.TYPE_HELMETS_ID)]
        item_stats = []
        self.damage = 9 + self.lvl
        self.armor = 0 + (self.lvl // d.PLAYER_RESISTS_DIVISOR)
        self.emp = 0
        self.punch = 0
        self.razriv = 0
        self.radiation = 0
        self.chemical_burn = 0
        self.blast = 0
        self.shot = 0
        self.regen = 0 + (self.lvl // d.PLAYER_RESISTS_DIVISOR)
        self.max_hp = 90 + (10 * self.lvl)
        self.current_hp = self.max_hp
        self.crit_chance = 0
        self.penetrate = 0
        self.chance_to_hit = 50 + (self.lvl // d.PLAYER_RESISTS_DIVISOR)
        self.dodge = 0 + (self.lvl // d.PLAYER_RESISTS_DIVISOR)
        self.skills = min(1 + (self.lvl // d.PLAYER_RESISTS_DIVISOR), len(d.ALL_SKILLS))
        for i in all_active_items:  # 00 - params, 01 - mods, 1 - type
            if not (type(i[0]) == int):
                if type(i[0][1]) == list:
                    for j in i[0][1]:
                        mod_temp = get_all_mode_params(cursor, i[1], j)
                        i[0][0] = append_mode_params(i[0][0], mod_temp)
                item_stats.append(i[0][0])
        for i in item_stats:
            weapons_bust_params_attr = [self.damage, self.crit_chance, self.chance_to_hit, self.penetrate]
            armors_bust_params_attr = [self.armor, self.emp, self.punch, self.razriv, self.radiation,
                                       self.chemical_burn, self.blast, self.shot, self.regen, self.max_hp, self.dodge]
            if len(i) - d.COUNT_NO_CHANGED_ITEM_PARAMS - 1 == len(d.WEAPONS_BUST_PARAMS_NAME):
                temp = i[d.START_CHANGED_PARAMETERS + 1:d.PRICE_NUMBER]
                self.damage_type = max(i[2], self.damage_type)
                for j in range(len(temp)):
                    temp_param = weapons_bust_params_attr[j] + temp[j]
                    setattr(self, d.WEAPONS_BUST_PARAMS_NAME[j], temp_param)
            elif len(i) - d.COUNT_NO_CHANGED_ITEM_PARAMS == len(d.ARMORS_BUST_PARAMS_NAME):
                temp = i[d.START_CHANGED_PARAMETERS:d.PRICE_NUMBER]
                for j in range(len(temp)):
                    temp_param = armors_bust_params_attr[j] + temp[j]
                    setattr(self, d.ARMORS_BUST_PARAMS_NAME[j], temp_param)
        self.current_hp = self.max_hp
        self.items_rating = (self.damage + self.armor + self.lvl + self.regen) * 10 + (
                self.max_hp + len(self.items_obj)) * 2
        self.data_change(cursor)
        self.img_ready = False

    def refresh_inventory(self, cursor):
        self.items_obj = []
        self.get_inventory(False, cursor)

    def update_database_value(self, cursor, value, param):
        res = param
        if not str(param).isdigit():
            res = f'\'{res}\''
        result = f"UPDATE users SET {value[1]} = {res} WHERE user_id = {self.user_id}"
        cursor.execute(result)
        setattr(self, value[1], param)

    def update_database_values(self, cursor, value, param):
        for i in range(len(value)):
            result = f"UPDATE users SET {value[i][1]} = {param[i]} WHERE user_id = {self.user_id}"
            cursor.execute(result)
            setattr(self, value[i][1], param[i])

    def character_image_generator(self, cursor):
        left_hand_weapon = 0
        right_hand_weapon = 0
        item_armor = 0
        artefact = 0
        helmet = 0
        if self.background == 0:
            res = get_database_params_from_id("locations", [d.FILENAME_NUMBER], self.location, cursor)
        else:
            res = get_database_params_from_id("background", [d.FILENAME_NUMBER], self.background, cursor)
        background = check_image_valid(str(res[0]), d.BACKGROUND_IMAGE_PATH)
        cursor.execute('SELECT skin_id, filename from skins')
        all_skins = cursor.fetchall()
        skin_src = None
        for skin in all_skins:
            if skin[0] == self.skin:
                skin_src = skin[1]
                break
        if not skin_src:
            return
        player_skin = check_image_valid(skin_src, d.SKINS_IMAGE_PATH)
        param_table = check_image_valid(d.DEFAULT_PARAM_TABLE)
        if not (self.skin in d.NO_ITEM_SKINS):
            if self.left_hand != 0:  # места не связанные с инвентарём не рефакторить, смысла особо нету
                res = get_database_params_from_id("items_param", [d.ITEMS_PARAM_PROTO_ID], self.left_hand, cursor)
                res_buffer = get_database_item_param_from_name(d.TYPE_WEAPONS_NAME, d.DEFAULT_NAME_FILENAME_LINE, res[0],
                                                               cursor)
                left_hand_weapon = check_image_valid(str(res_buffer) + '_LEFT', d.WEAPONS_IMAGE_PATH)
            if self.right_hand != 0:
                res = get_database_params_from_id("items_param", [d.ITEMS_PARAM_PROTO_ID], self.right_hand, cursor)
                res_buffer = get_database_item_param_from_name(d.TYPE_WEAPONS_NAME, d.DEFAULT_NAME_FILENAME_LINE, res[0],
                                                               cursor)
                right_hand_weapon = check_image_valid(str(res_buffer) + '_RIGHT', d.WEAPONS_IMAGE_PATH)
            if not (self.skin in d.ONLY_WEAPON_SKINS):
                if self.active_armor != 0:
                    res = get_database_params_from_id("items_param", [d.ITEMS_PARAM_PROTO_ID], self.active_armor,
                                                      cursor)
                    res_buffer = get_database_item_param_from_name(d.TYPE_ARMOR_NAME, d.DEFAULT_NAME_FILENAME_LINE, res[0],
                                                                   cursor)
                    item_armor = check_image_valid(str(res_buffer), d.ARMORS_IMAGE_PATH)
                if self.helmet != 0:
                    res = get_database_params_from_id("items_param", [d.ITEMS_PARAM_PROTO_ID], self.helmet, cursor)
                    res_buffer = get_database_item_param_from_name(d.TYPE_HELMETS_NAME, d.DEFAULT_NAME_FILENAME_LINE,
                                                                   res[0],
                                                                   cursor)
                    helmet = check_image_valid(str(res_buffer), d.HELMETS_IMAGE_PATH)
        if self.active_artefact != 0:
            res = get_database_params_from_id("items_param", [d.ITEMS_PARAM_PROTO_ID], self.active_artefact, cursor)
            res_buffer = get_database_item_param_from_name(d.TYPE_ARTEFACTS_NAME, d.DEFAULT_NAME_FILENAME_LINE, res[0],
                                                           cursor)
            artefact = check_image_valid(str(res_buffer), d.ARTEFACTS_IMAGE_PATH)
        data = [player_skin, param_table, left_hand_weapon, right_hand_weapon, item_armor, artefact, helmet]
        for i in range(len(data)):
            if not data[i]:
                continue
            background = Image.alpha_composite(background.convert('RGBA'), data[i].convert('RGBA'))
        font = ImageFont.truetype(font=d.DEFAULT_FONT_FULL_PATH, size=18, index=0, encoding='', layout_engine=None)
        font2 = ImageFont.truetype(font=d.DEFAULT_FONT_FULL_PATH, size=22, index=0, encoding='', layout_engine=None)
        draw_text = ImageDraw.Draw(background)
        draw_text.text(
            (80 - (len(self.user_name) * 5), 21),
            self.user_name,
            # Добавляем шрифт к изображению
            font=font2,
            fill='#ffffff')
        draw_text.text(
            (13, 145),
            f'Атака: {self.damage}\nЗащита: {self.armor}\nКрит-шанс: {self.crit_chance}\nЛечение: {self.regen}\nЗдоровье: {self.max_hp}',
            # Добавляем шрифт к изображению
            font=font,
            fill='#ffffff')
        # for j in range(len(data)):  # предполагается, что они сами закроются после завершения потока
        #     if data[j]:
        #         data[j].close()
        image_handle = io.BytesIO()
        background.save(image_handle, "PNG")
        image_handle.seek(0)
        return image_handle

    def generate_item_list_for_inventory(self):
        result = ''
        # item_data = []
        last_item = min(len(self.items_obj), (self.inventory_page + 1) * d.ITEMS_IN_ONE_PAGE)
        if self.inventory_page * d.ITEMS_IN_ONE_PAGE > len(self.items_obj):
            return
        for i in range(self.inventory_page * d.ITEMS_IN_ONE_PAGE, last_item):
            item = self.items_obj[i]
            result += f'{d.ALL_TYPE_EMOJI[item.type]} {i - (self.inventory_page * d.ITEMS_IN_ONE_PAGE) + 1}) {item.name}\n'
            if item.is_stackable():
                result = result[:-1] + f', {item.count} шт.\n'

        #     if not item.is_stackable():
        #         temp = get_database_params_from_id("items_param", d.ITEMS_PARAM_FULL, self.items[i], cursor)
        #         item_data.append([get_database_item_param_from_name(d.ALL_TYPE_NAMES[temp[d.ITEMS_PARAM_TYPE]],
        #                                                             d.DEFAULT_NAME_ITEM_NAMES,
        #                                                             [temp[d.ITEMS_PARAM_PROTO_ID]], cursor),
        #                           temp[d.ITEMS_PARAM_TYPE]])
        #     elif type(self.items[i]) == list:
        #         item_data.append([get_stackable_item_name(cursor, self.items[i]), self.items[i][1],
        #                           d.STACKABLE_TYPE[self.items[i][0] // d.BONUS_INTO_ID]])
        # for i in range(len(item_data)):
        #     if len(item_data[i]) == 2:
        #         buffer = d.ALL_TYPE_EMOJI[item_data[i][1]] + ' ' + str(i + 1) + ') ' + item_data[i][0] + '\n'
        #         result = result + buffer
        #     elif len(item_data[i]) == 3:
        #         buffer = d.ALL_TYPE_EMOJI[item_data[i][2]] + ' ' + str(i + 1) + ') ' + item_data[i][0] + ', ' + str(
        #             item_data[i][1]) + ' шт. \n'
        #         result = result + buffer
        # res_str = result.replace('_', ' ')
        return result

    def remove_item_from_items(self, cursor, item_id):  # не рефакторить
        param = None
        cursor.execute(f"SELECT * from items WHERE user_id = {self.user_id}")
        for i in cursor:
            for j in range(len(i)):
                if i[j] == item_id:
                    param = j
                    break
        result = f"UPDATE items SET item{param} = 0 WHERE user_id = {self.user_id}"
        cursor.execute(result)
        buf = 0
        result = f"SELECT item{self.lastitem} from items WHERE user_id = {self.user_id}"
        cursor.execute(result)
        for i in cursor:
            buf = int(i[0])
        result = f"UPDATE items SET item{self.lastitem} = 0 WHERE user_id = {self.user_id}"
        cursor.execute(result)
        result = f"UPDATE items SET item{param} = {buf} WHERE user_id = {self.user_id}"
        cursor.execute(result)
        self.lastitem -= 1

    def move_item_from_skin(self, cursor, connect, name):
        item = getattr(self, name[1])
        setattr(self, name[1], 0)
        self.update_database_value(cursor, name, 0)
        if item != 0:
            result = f"UPDATE items SET item{self.lastitem + 1} = {item} Where user_id = {self.user_id}"
            cursor.execute(result)
            self.lastitem += 1
            self.items_obj.append(Item(item, cursor))
            connect.commit()
            self.calculate_player_parameters(cursor)
            return True
        return False

    def move_items_from_skin(self, cursor, connect):
        left_hand = self.left_hand
        right_hand = self.right_hand
        armor = self.active_armor
        artefact = self.active_artefact
        helmet = self.helmet
        self.left_hand = 0
        self.right_hand = 0
        self.active_armor = 0
        self.active_artefact = 0
        self.helmet = 0
        self.update_database_values(cursor, [d.PLAYER_LEFT_HAND, d.PLAYER_RIGHT_HAND,
                                             d.PLAYER_ARMOR_ITEM, d.PLAYER_ARTEFACT, d.PLAYER_HELMET], [0, 0, 0, 0, 0])
        params = [left_hand, right_hand, armor, artefact, helmet]
        for i in range(len(params)):
            if params[i] != 0:
                result = f"UPDATE items SET item{self.lastitem + 1} = {params[i]} Where user_id = {self.user_id}"
                cursor.execute(result)
                self.lastitem += 1
                self.items_obj.append(Item(params[i], cursor))
        connect.commit()
        self.calculate_player_parameters(cursor)

    def move_item_to_skin(self, cursor, connect):
        item_hand = 0  # 0 лево, 1 право
        item_path = []
        item = self.selected_item
        # item_id = self.items[self.selected_item[0]]
        # item_type = self.selected_item[1]
        if not (item.type in d.ITEMS_CAN_PUT) or item.is_broken():
            return d.NO_STACK_ERROR
        if (item.type == d.TYPE_WEAPONS_ID and self.left_hand and self.right_hand) or (item.is_armor()
                                                                                       and self.active_armor) or (
                item.type == d.TYPE_HELMETS_ID and self.helmet) or (item.is_artefact()
                                                                    and self.active_artefact):
            return d.SLOT_IS_BUSY_ERROR
        if item.is_weapon():  # ультрахард, лучше просчитать оружие отдельно
            if not self.left_hand:
                item_hand = 0
            else:
                item_hand = 1
            item_path = d.ITEMS_SKIN_ASSOCIATION[item.type][item_hand]
        else:
            item_path = d.ITEMS_SKIN_ASSOCIATION[item.type]
        result = f"UPDATE users SET {item_path[1]} = {item.id} Where user_id = {self.user_id}"
        cursor.execute(result)
        self.remove_item_from_items(cursor, item.id)
        connect.commit()
        self.stat_parse(cursor)
        self.remove_item_obj(item.id)
        self.calculate_player_parameters(cursor)
        return d.SUCCESSFUL

    # def add_item(self, cursor, adding_loot):
    #     if adding_loot[1] in d.STACKABLE_TYPE:
    #         if len(adding_loot) == 2:
    #             adding_loot.append(1)
    #         self.add_st_item(adding_loot, cursor)
    #     else:
    #         self.add_item_to_database(proto_type=adding_loot, cursor=cursor)

    def look_all_items_param(self, param, cursor):
        number = (param + self.inventory_page * d.ITEMS_IN_ONE_PAGE)
        try:
            item = self.items_obj[number - 1]
        except IndexError:
            return d.ITEM_NOT_FOUND_ERROR
        res_str = item.draw_params(cursor)
        self.selected_item = item
        item_art = item.source
        if item_art != 'n':
            image_handle = item_art
        else:
            image_handle = d.DEFAULT_PICTURE_VK
        custom_keyboard = [25, (d.KEYBOARD_SET_SELECTED_ITEM[1] if item.is_clothes() else None),
                           (d.KEYBOARD_SET_SELECTED_ITEM[2] if item.is_have_mods() else None),
                           d.KEYBOARD_SET_SELECTED_ITEM[3],
                           d.KEYBOARD_SET_SELECTED_ITEM[4],
                           (d.KEYBOARD_SET_SELECTED_ITEM[5] if item.is_loot_case() else None),
                           (d.KEYBOARD_SET_SELECTED_ITEM[6] if item.is_can_broken() else None),
                           (d.KEYBOARD_SET_SELECTED_ITEM[7] if item.is_can_use() else None),
                           ]
        custom_keyboard = list(filter(None, custom_keyboard))
        return [image_handle, res_str, custom_keyboard]

        # result = ''
        # item_iznos = 0
        # item_mods = []
        # number = (param + self.inventory_page * d.ITEMS_IN_ONE_PAGE)
        # if type(self.items[number - 1]) == list:
        #     data = get_all_stackable_item_params(cursor, self.items[number - 1])
        #     item_type = d.STACKABLE_TYPE[self.items[number - 1][0] // d.BONUS_INTO_ID]
        # else:
        #     data = get_database_params_from_id('items_param', d.ITEMS_PARAM_FULL, self.items[number - 1], cursor)
        #     item_type = data[d.ITEMS_PARAM_TYPE]
        #     item_iznos = data[d.ITEMS_PARAM_IZNOS]
        #     for i in range(d.START_PARAM_MODS, d.END_PARAM_MODS):
        #         if data[i]:
        #             item_mods.append(i - len(d.ITEMS_PARAM_ALL) + 1)
        #     temp = get_all_no_stack_item_params(d.ALL_TYPE_NAMES[item_type], data[d.ITEMS_PARAM_PROTO_ID], cursor)
        #     for i in range(len(item_mods)):
        #         mod_temp = get_all_mode_params(cursor, item_type, item_mods[i])
        #         temp = append_mode_params(temp, mod_temp)
        #     data = temp
        # params = d.ALL_ITEM_SIGNATURES[item_type]
        # for j in range(len(params)):
        #     # костыль для отрисовки типа урона
        #     if item_type == d.TYPE_WEAPONS_ID and j + 1 == 2:
        #         buffer = f'{d.DAMAGE_TYPES_EMOJI[data[j + 1]]} {params[j]}: {d.DAMAGE_TYPES[data[j + 1]]}\n'
        #         result = result + buffer
        #         continue
        #     if item_type in d.UPGRADE_TYPES and j + 1 == 2:
        #         buffer = f'⚙ Тип улучшения: {d.ALL_TYPE_NAMES[item_type]}\n'
        #         result = result + buffer
        #
        #     if data[j + 1] != 0:
        #         buffer = f'{params[j]}: {data[j + 1]}\n'
        #         result = result + buffer
        # result += f'🤝 Цена продажи: {data[d.PRICE_NUMBER] // d.ITEMS_SALE_PENALTY}\n'
        # if item_iznos != 0:
        #     buffer = f'🔧 Прочность: {item_iznos}\n'
        #     result = result + buffer
        # for k in range(len(item_mods)):
        #     buffer = f'⚙ Мод {k + 1}: {get_mode_name(cursor, item_type, item_mods[k])}\n'
        #     result = result + buffer
        # res_str = result.replace('_', ' ')
        # self.selected_item = [number - 1, item_type, data[d.PRICE_NUMBER] // d.ITEMS_SALE_PENALTY]
        # item_art = data[d.SOURCE_NUMBER]
        # if item_art != 'n':
        #     image_handle = item_art
        # else:
        #     image_handle = d.DEFAULT_PICTURE_VK
        # custom_keyboard = [25, (d.KEYBOARD_SET_SELECTED_ITEM[1] if item_type in d.ITEMS_CAN_PUT else None),
        #                    (d.KEYBOARD_SET_SELECTED_ITEM[2] if item_type in d.ITEMS_CAN_PUT else None),
        #                    d.KEYBOARD_SET_SELECTED_ITEM[3],
        #                    (d.KEYBOARD_SET_SELECTED_ITEM[4] if not (item_type in d.STACKABLE_TYPE) else None),
        #                    (d.KEYBOARD_SET_SELECTED_ITEM[5] if (item_type == d.TYPE_LOOT_CASES_ID) else None),
        #                    ]
        # custom_keyboard = list(filter(None, custom_keyboard))
        # return [image_handle, res_str, custom_keyboard]

    def get_valid_mode_list(self, cursor):
        custom_keyboard = [26]
        result = '💣 Выбирай, какой мод добавить:\n'
        item = self.selected_item
        mode_list = []
        if not item.is_have_mods():
            return d.NO_STACK_ERROR
        for mode in self.items_obj:
            if mode.is_upgrades():
                if mode.type == item.get_mode_type():
                    mode_list.append(mode)
        if not mode_list:
            return d.NO_HAVE_MODS_ERROR
        for mode in mode_list:
            buffer = f'⚙ {mode.name}, {mode.count} шт.\n'
            result = result + buffer
            custom_keyboard.append(f'{d.ALL_TYPE_EMOJI[item.type]} {mode.name} ({mode.proto_id})')
        # item_id = self.items[self.selected_item[0]]
        # item_type = self.selected_item[1]
        # mode_list = []
        # if not (item_type in d.ITEMS_CAN_HAVE_MODS):
        #     return d.NO_STACK_ERROR
        # for i in self.items:
        #     if type(i) == list:
        #         if d.STACKABLE_TYPE[i[0] // d.BONUS_INTO_ID] == d.ITEM_ASSOCIATIONS[item_type]:
        #             mode_list.append(i)
        return [result.replace('_', ' '), custom_keyboard]

    def add_mod_to_item(self, mod_id, is_free, cursor):
        item_num = 0
        mode = None
        item = self.selected_item
        if not is_free:
            mode = self.get_item_by_pid(mod_id, item.get_mode_type())
            if not mode:
                return d.ITEM_NOT_FOUND_ERROR
        changed_item_uid = item.id
        # item_type = item.get_mode_type()
        # mod_type = d.STACKABLE_TYPE[mod_id // d.BONUS_INTO_ID]
        # if item_type != mod_type:
        #     return d.ITEM_NOT_FOUND_ERROR
        # for check_err in cursor.execute(
        #         f'SELECT mods{mod_id % d.BONUS_INTO_ID} FROM items_param WHERE id = {changed_item_uid}'):
        #     if not (check_err[0] is None):
        if item.is_mode_busy(mod_id):
            return d.SLOT_IS_BUSY_ERROR
        item.add_mode_to_item(mod_id, cursor)
        if not is_free:
            self.update_count_stack_item(cursor, mode, -1, False)
        return d.SUCCESSFUL

    def update_user_balance(self, cursor, bonus):
        self.balance += (bonus * 2) if self.premium else bonus
        self.balance = clamp(self.balance, 0, 0x7fffffff)
        self.update_database_value(cursor, d.PLAYER_BALANCE, self.balance)

    def destroy_no_stack_item(self, cursor, item):
        self.remove_item_from_items(cursor, item.id)
        self.items_obj.remove(item)
        cursor.execute(f'DELETE FROM items_param WHERE id = {item.id}')

    def update_count_stack_item(self, cursor, item, bonus, reset_it=True):
        item_id = item.id
        item_count = item.count
        new_count = item_count + bonus
        if new_count < 0:
            return d.ERROR
        cursor.execute(f"UPDATE items_param SET count = {new_count} WHERE id = {item_id}")
        item.count = new_count
        if new_count == 0:
            self.destroy_no_stack_item(cursor, item)
            if reset_it:
                self.selected_item = None
            return d.ITEM_WAS_REMOVED
        return d.SUCCESSFUL

    def inline_keyboard(self, text, answers_list, image=None, is_edit=False, is_callback=False):
        keyboard = VkKeyboard(inline=True)
        msg_len = len(answers_list) - 1
        func = keyboard.add_callback_button if is_callback else keyboard.add_button
        for i in range(1, len(answers_list)):
            if answers_list[i] is None:
                continue
            func(answers_list[i], color=VkKeyboardColor.PRIMARY,
                 payload=f'{answers_list[0] * d.PAYLOAD_MULTIPLIER + i - 1}')  # payload позволяет узнать кнопку по идентификатору, используется не полностью
            if msg_len == 4 or msg_len == 6 or msg_len >= 7:
                if i % 2 == 0 and i < msg_len:
                    keyboard.add_line()
            elif msg_len == 3 or msg_len == 5:
                if i < msg_len:
                    keyboard.add_line()
            elif msg_len == 2 and i < msg_len:
                keyboard.add_line()
        message = text
        if self.send_message(message, keyboard.get_keyboard(), image, is_edit=is_edit) == d.MESSAGE_SEND_ERROR:
            return d.MESSAGE_SEND_ERROR
        self.keyboard = answers_list[0]

    def sell_item_default(self, cursor):
        item = self.selected_item
        if item.count > 1:
            return d.NEED_MORE_DATA_ERROR
        self.sell_item_default_continue(cursor, 0)
        return self.balance

    def sell_item_default_continue(self, cursor, count):
        item = self.selected_item
        if count == 0:
            self.destroy_no_stack_item(cursor, item)
            self.update_user_balance(cursor, item.get_price())
        else:
            if count > item.count:
                return d.NOT_ENOUGH_ITEMS_ERROR
            copy = item.get_price()
            self.update_count_stack_item(cursor, item, -count)
            self.update_user_balance(cursor, copy * count)
        return self.balance

    def move_item_to_auction(self, cursor, price):
        item = self.selected_item
        item_owner = self.user_id
        if item.count > 1:
            item.update_count(-1, cursor)
            uid = self.add_item_to_database(proto_type=(item.proto_id, item.type, 1), cursor=cursor, new_id=True)
            item = self.get_item_obj(uid)
        self.remove_item_from_items(cursor, item.id)
        self.items_obj.remove(item)
        cursor.execute(f'insert into auction (item_id, name, owner_id, price) '
                       f'values ({item.id},\'{item.name}\',{item_owner},{price}) ON CONFLICT DO NOTHING')

    def move_item_from_auction(self, cursor, uid=0):
        if uid == 0 and not self.temp_data:
            return
        item_id = uid if uid > 0 else self.temp_data[1]
        item_ = Item(item_id, cursor)
        item_type = item_.type
        item_proto = item_.proto_id
        if item_.is_stackable():
            for item in self.items_obj:
                if item.type == item_type and item_proto == item.proto_id:
                    item.update_count(1, cursor)
                    cursor.execute(f'DELETE FROM auction WHERE item_id = {item_id}')
                    cursor.execute(f'DELETE FROM items_param WHERE id = {item_id}')
                    return item
        result = f"UPDATE items SET item{self.lastitem + 1} = {item_id} Where user_id = {self.user_id}"
        cursor.execute(result)
        self.lastitem += 1
        self.items_obj.append(Item(item_id, cursor))
        cursor.execute(f'DELETE FROM auction WHERE item_id = {item_id}')

    def return_all_user_items(self, cursor):
        cursor.execute(f'SELECT item_id from auction WHERE owner_id = {self.user_id}')
        item_uids = cursor.fetchall()
        for uid in item_uids:
            self.move_item_from_auction(cursor, uid=uid[0])
        return

    def get_user_lots(self, cursor):
        self.temp_data.clear()
        self.temp_data.append(d.LOTS_ID_FROM_AUCTION)
        result = ''
        custom_keyboard = d.KEYBOARD_INVENTORY.copy()
        custom_keyboard[0] = 29
        number = 1
        cursor.execute(f'SELECT * from auction WHERE owner_id = {self.user_id}')
        res = cursor.fetchall()
        res_2 = res[
                self.auction_page * d.ITEMS_IN_ONE_PAGE:self.auction_page * d.ITEMS_IN_ONE_PAGE + d.ITEMS_IN_ONE_PAGE]
        if not res_2:
            self.auction_page = max(0, self.auction_page - 1)
            res_2 = res[
                    self.auction_page * d.ITEMS_IN_ONE_PAGE:self.auction_page * d.ITEMS_IN_ONE_PAGE + d.ITEMS_IN_ONE_PAGE]
        for i in res_2:
            buffer = f'{number}) {i[1]}, цена: {i[3]}💰\n'
            result = result + buffer
            self.temp_data.append(i[0])
            number += 1
        return [result, custom_keyboard]

    def draw_selected_auction_lot(self, cursor, uid):
        self.temp_data.clear()
        self.temp_data.append(d.SELECTED_LOT_FROM_AUCTION)
        self.temp_data.append(uid)
        item = Item(uid, cursor)
        res_str = item.draw_params(cursor)
        cursor.execute(f'SELECT price from auction WHERE item_id={uid}')
        data = cursor.fetchall()[0][0]
        res_str += f'💰 Цена лота: {data}'
        item_art = item.source
        if item_art != 'n':
            image_handle = item_art
        else:
            image_handle = d.DEFAULT_PICTURE_VK
        return [image_handle, res_str]

    def look_auction_lots(self, cursor):
        data = [self.balance, self.user_id]
        temp = []
        result = []
        cursor.execute(f'SELECT * FROM auction WHERE price < {self.balance} AND owner_id != {self.user_id} ORDER BY price DESC LIMIT 8')
        for i in cursor:
            temp.append(i[0])
        for j in temp:
            result.append(self.draw_selected_auction_lot(cursor, j))
        self.temp_data.clear()
        self.temp_data.append(d.SOME_ITEMS_FROM_AUCTION)
        for k in temp:
            self.temp_data.append(k)
        return result

    def buy_item_from_auction(self, uid, cursor):
        params = []
        cursor.execute(f'SELECT * FROM auction WHERE item_id = {uid}')
        for i in cursor:
            params = i
        if not params:
            return d.ITEM_NOT_FOUND_ERROR
        price = params[3]
        if price > self.balance:
            return d.ERROR
        seller = player_connect(params[2], cursor)
        item = self.move_item_from_auction(cursor, uid)
        if not item:
            item = Item(uid, cursor)
        item.update_param('owner_id', self.user_id, cursor)
        self.update_user_balance(cursor, -price)
        seller.update_user_balance(cursor, price)
        return seller

    def get_lots_from_name(self, message, cursor):
        temp = []
        result = []
        data = f'SELECT * FROM auction WHERE name LIKE \'%{message}%\' AND owner_id != {self.user_id} LIMIT 8'
        cursor.execute(data)
        for i in cursor:
            temp.append(i[0])
        for j in temp:
            result.append(self.draw_selected_auction_lot(cursor, j))
        self.temp_data.clear()
        self.temp_data.append(d.SOME_ITEMS_FROM_AUCTION)
        for k in temp:
            self.temp_data.append(k)
        return result

    def transfer_money(self, recipient_id, money, cursor):
        recipient = None
        if recipient_id == self.user_id:
            return
        cursor.execute('SELECT * FROM users')
        for row in cursor:
            if row[0] == recipient_id:
                # if not (recipient_id in d.active_users):
                #     recipient = Stalker(recipient_id, cursor, False)
                # else:
                #     recipient = d.get_player(recipient_id)
                recipient = player_connect(recipient_id, cursor)
                break
        if not recipient:
            return d.PLAYER_NOT_FOUND_ERROR
        if money > self.balance:
            return d.NEED_MORE_MONEY_ERROR
        self.update_user_balance(cursor, -money)
        recipient.update_user_balance(cursor, money)
        return recipient

    def get_inventory(self, first, cursor):
        if first:
            firstloot = [d.WEAPON_KORA909, d.REWARD_CASE_DEFAULT]
            for i in range(len(firstloot)):
                # if firstloot[i][1] in d.STACKABLE_TYPE:
                #     self.add_st_item(firstloot[i], cursor)
                # else:
                self.add_item_to_database(proto_type=firstloot[i], cursor=cursor)
        else:
            string = "SELECT * from items WHERE user_id = " + str(self.user_id)
            cursor.execute(string)
            for row in cursor:
                for j in range(d.START_PLAYER_ITEMS, d.END_PLAYER_ITEMS):
                    if row[j]:
                        self.items_obj.append(Item(row[j], cursor))
                # for ji in range(d.START_PLAYER_ITEMS_ST, d.END_PLAYER_ITEMS_ST):
                #     if row[ji]:
                #         self.items.append([ji - d.MAX_ITEMS, row[ji]])

    def get_item_rating(self, cursor):
        return self.get_arena_rating(cursor, is_rating=True)

    def get_arena_rating(self, cursor, is_rating=False, is_top=False):
        self.rating_lst = [is_rating]
        # count = 0
        result = '🏆 Топ Арены:\n' if not is_rating else '🏆 Топ Сталкеров:\n'
        tmp = 'rating' if not is_rating else 'items_rating'
        cursor.execute(f'SELECT row_number() OVER(ORDER BY {tmp} DESC) as id, user_id, user_name, {tmp} from users')
        res = cursor.fetchall()
        if not is_top:
            for i in range(len(res)):
                if self.user_id == res[i][1]:
                    res = res[max(0, i - 3):min(i + 5, len(res))]
                    break
        else:
            res = res[0:min(8, len(res))]
        for i in res:
            self.rating_lst.append(i[1])
            if i[1] in d.ADMINISTRATORS:
                i = list(i)
                i[1] = 1
            buffer = f'{i[0]}) Имя: [id{i[1]}|{i[2]}], рейтинг: {i[3]}\n'
            result = result + buffer
            # count += 1
        return result

    def show_player_skills(self):
        result = ''
        if self.skills > len(d.ALL_SKILLS):
            print('skills error')
            return
        for i in range(1, self.skills + 1):
            data = d.ALL_SKILLS[i]
            buffer = f'{data[0]}.\n{data[1]}.\n\n'
            result = result + buffer
        return result

    def check_lvl_up(self, cursor):
        while self.opit >= 100 + 100 * self.lvl:
            self.opit -= 100 + 100 * self.lvl
            self.lvl += 1
            self.update_database_value(cursor, d.PLAYER_LVL, self.lvl)
            self.update_database_value(cursor, d.PLAYER_OPIT, self.opit)
            self.send_message('🔥 Ты получил новый уровень!', attachment='video-210036099_456239019')
            self.calculate_player_parameters(cursor)
        else:
            self.update_database_value(cursor, d.PLAYER_OPIT, self.opit)

    def send_message(self, text, keyb=d.BASE_KEYBOARD_DATA, attachment=None, is_edit=False, template=None):
        bool_test = True if (is_edit and self.last_edit_message) else False
        d.MESSAGES_QUEUE.put(['messages.edit' if bool_test else 'messages.send',
                              {'peer_id': self.peer_id if self.peer_id != 0 else self.user_id,
                               'message': text,
                               'message_id': self.last_edit_message if bool_test else None,
                               'random_id': int(time.time() * 1000000),
                               'keyboard': keyb,
                               'attachment': attachment,
                               'template': template}, self.user_id])
        return 0
        # func = d.GIVE.messages.edit if bool_test else d.GIVE.messages.send
        # try:
        #     res = func(peer_id=(self.peer_id if self.peer_id != 0 else self.user_id),
        #          message=text,
        #          message_id=self.last_edit_message if bool_test else None,
        #          random_id=int(time.time() * 1000000),
        #          keyboard=keyb,
        #          attachment=attachment,
        #          template=template
        #          )
        # except exceptions.ApiError:
        #     if not self.last_peer_id:
        #         return d.MESSAGE_SEND_ERROR
        #     try:
        #         res = func(peer_id=self.last_peer_id,
        #              message=text,
        #              message_id=self.last_edit_message if bool_test else None,
        #              random_id=int(time.time() * 1000000),
        #              keyboard=keyb,
        #              attachment=attachment,
        #              template=template
        #                    )
        #     except exceptions.ApiError:
        #         return d.MESSAGE_SEND_ERROR
        # except Rexceptions.ConnectionError:
        #     d.restart_connection()
        #     return d.MESSAGE_SEND_ERROR
        # if not bool_test:
        #     self.last_edit_message = res
        # return res

    def get_location_bosses(self, cursor):
        result = '🐲 Боссы текущей локации:\n'
        number = 1
        count = 0
        string = f"SELECT * from bosses WHERE user_id > {(self.location - 1) * d.MAX_BOSSES_IN_LOCATION} and user_id <= {self.location * d.MAX_BOSSES_IN_LOCATION}"
        cursor.execute(string)
        for row in cursor:
            if number == 1 and cursor.rowcount == 0:
                return d.ERROR
            result += str(number) + ') ' + row[1] + '\n'
            count = number
            number += 1
        if result == '🐲 Боссы текущей локации:\n':
            return d.ERROR
        return [result.replace('_', ' '), count]

    def get_boss_date(self, message, cursor):
        number = d.EMOJI_NUMBER_ASSOTIATIONS[message]
        if not number or type(number) != int:
            return d.ERROR
        boss_id = (self.location - 1) * d.MAX_BOSSES_IN_LOCATION + number
        string = "SELECT * from bosses WHERE user_id = " + str(boss_id)
        data = None
        cursor.execute(string)
        for row in cursor:
            data = row
            break
        if not data:
            return d.ERROR
        name = str(data[d.BOSS_USERNAME[0]])
        damage = str(data[d.BOSS_DAMAGE[0]])
        hp = str(data[d.BOSS_MAX_HP[0]])
        boss_art = str(data[d.BOSS_SOURCE[0]])
        reward = d.ALL_BOSSES_REWARD[data[d.BOSS_ID[0]]]
        reward_msg = '🔥 Возможные награды:\n'
        for reward_part in reward:
            if reward_part[1] == d.MINI_BOSS_REWARD:
                reward_msg += f'&#8195;&#8195;{reward_part[0]}💰\n'
                continue
            elif reward_part[1] < len(d.ALL_TYPE_NAMES):
                rew_name = get_item_name_proto(cursor, reward_part[0], reward_part[1])
                reward_msg += f'&#8195;&#8195;{d.ALL_TYPE_EMOJI[reward_part[1]]} {rew_name}\n'
            elif reward_part[1] == d.TYPE_REWARDS_SKIN:
                reward_msg += f'&#8195;&#8195;🎭 Скин {reward_part[2]}\n'
            elif reward_part[1] == d.TYPE_REWARDS_BACKGROUND:
                reward_msg += f'&#8195;&#8195;🌄 Фон {reward_part[2]}\n'
        result = f'📋 Имя: {name}\n🔪 Урон: {damage}\n❣ Здоровье: {hp}\n'
        result += reward_msg
        result += 'Подробные характеристики скрыты.\n'
        if boss_art != 'n':
            image_handle = boss_art
        else:
            image_handle = d.DEFAULT_PICTURE_VK
        res_str = result.replace('_', ' ')
        self.selected_boss = data[d.BOSS_ID[0]]
        return [image_handle, res_str]

    def get_user_group(self, cursor):
        data = None
        if self.group_id == 0:
            return d.PLAYER_NOT_HAVE_GROUP_ERROR
        string = "SELECT * from groups WHERE group_id = " + str(self.group_id)
        result = '👥 Ваша группа:\n'
        count = 1
        cursor.execute(string)
        for row in cursor:
            data = row
            break
        if not data:
            return d.ERROR
        for i in data[1:]:
            if i:
                player = player_connect(i, cursor)
                result += f'{count}) {player.src_name}\n'
                count += 1
        return [result, count - 1]

    def get_group_object(self, connect):
        cursor = connect.cursor()
        players_obj = []
        if self.group_id == 0:
            return
        group = Group([self], self.group_id, connect)
        if not group.group_id or not group.check_me(self):
            return
        group = group.get_list_id()
        for _id in group:
            if _id:
                player = player_connect(_id, cursor)
                if player:
                    players_obj.append(player)
        return players_obj

    def follow_user_to_group(self, follow_id, cursor, arena=False):
        if follow_id in d.active_users:
            follow_player = d.get_player(follow_id)
        else:
            follow_player = None
            cursor.execute('SELECT * FROM users')
            for row in cursor:
                if row[0] == follow_id:
                    follow_player = Stalker(follow_id, cursor, False)
                    # d.active_users.append(follow_id)
                    break
            if not follow_player:
                return d.PLAYER_NOT_FOUND_ERROR
        if not arena:
            if follow_player.group_id:
                return d.ERROR
            for follow_group in d.wait_group_follow:
                if follow_group[1] == follow_player:
                    return d.ERROR
            for player in d.auto_find_group:
                if follow_player.user_id == player.user_id:
                    return d.ERROR
            d.wait_group_follow.append([self, follow_player, time.time()])
        else:
            if follow_player.energy < d.ARENA_FIGHT_PRICE:
                return d.NEED_MORE_MONEY_ERROR
            for follow_group in d.wait_arena_follow:
                if follow_group[1] == follow_player:
                    return d.ERROR
                if follow_group[1] == self:
                    return d.SLOT_IS_BUSY_ERROR
                if self == follow_group[0]:
                    return d.NO_STACK_ERROR
            if follow_id in d.wait_arena_fight:
                return d.ERROR
            d.wait_arena_follow.append([self, follow_player, time.time()])
        return follow_player

    # def create_new_group(self, follow_user, connect):
    #     Group([self, follow_user], d.Global_Group_Id, connect)
    #     d.Global_Group_Id += 1
    #
    # def add_user_to_group(self, group_id, connect):
    #     Group([self], group_id, connect).add_to_group([self], connect.cursor())
    # free_slot = 0
    # string = "SELECT * from groups WHERE group_id = " + str(group_id)
    # for row in cursor.execute(string):
    #     for i in range(len(row)):
    #         if not row[i]:
    #             free_slot = i
    #             break
    # if not free_slot:
    #     return d.ERROR
    # data = [self.user_id, group_id]
    # string = "UPDATE groups SET player" + str(free_slot) + " = ? Where group_id = ?"
    # cursor.execute(string, data)
    # self.update_database_value(cursor, d.PLAYER_GROUP_ID, group_id)

    def follow_to_arena(self):
        data = None
        for follow_group in d.wait_arena_follow:
            if follow_group[1] == self:
                data = follow_group
                d.wait_arena_follow.remove(follow_group)
                break
        if not data:
            return d.ERROR
        leader = data[0]
        combat = Combat([self], [leader], d.COMBAT_TYPE_ARENA, add_rating=False)
        combat.add_combat_to_combats()
        return leader

    def follow_to_group(self, connect):
        cursor = connect.cursor()
        if self.group_id:
            return d.ERROR
        data = None
        for follow_group in d.wait_group_follow:
            if follow_group[1] == self:
                data = follow_group
                d.wait_group_follow.remove(follow_group)
                break
        if not data:
            return d.ERROR
        leader = data[0]
        if not leader.group_id:
            group = Group([self, leader], d.Global_Group_Id + 1, connect)
            if not group.group_id:
                return d.ERROR
            self.update_database_value(cursor, d.PLAYER_GROUP_ID, d.Global_Group_Id + 1)
            leader.update_database_value(cursor, d.PLAYER_GROUP_ID, d.Global_Group_Id + 1)
            d.Global_Group_Id += 1
        else:
            Group([self], leader.group_id, connect).add_obj_to_group([self], connect.cursor())
        if not self.group_id:
            return d.ERROR
        return leader

    def find_group(self, connect):
        cursor = connect.cursor()
        for player in d.auto_find_group:
            if player.user_id == self.user_id:
                player.send_message('❌ Ты уже в очереди')
                return
        d.auto_find_group.append(self)
        if len(d.auto_find_group) == 3:
            group = Group([d.auto_find_group[0], d.auto_find_group[1], d.auto_find_group[2]], d.Global_Group_Id + 1,
                          connect)
            if not group.group_id:
                d.auto_find_group.clear()
                return
            for player in d.auto_find_group:
                player.update_database_value(cursor, d.PLAYER_GROUP_ID, d.Global_Group_Id + 1)
                player.send_message('👥 Группа успешно сформирована')
            d.Global_Group_Id += 1
            d.auto_find_group.clear()
        else:
            return d.SUCCESSFUL

    def leave_from_group(self, connect):
        if not self.group_id:
            return
        group = Group([self], self.group_id, connect)
        return group.remove_with_group(self, connect.cursor())
        # free_slot = 0
        # string = "SELECT * from groups WHERE group_id = " + str(self.group_id)
        # for row in cursor.execute(string):
        #     for i in range(len(row)):
        #         if row[i] == self.user_id:
        #             free_slot = i
        #             break
        # if not free_slot:
        #     return d.ERROR
        # data = [0, self.group_id]
        # string = f"UPDATE groups SET player{free_slot} = ? Where group_id = ?"
        # cursor.execute(string, data)
        # self.update_database_value(cursor, d.PLAYER_GROUP_ID, 0)
        # return d.SUCCESSFUL

    def answer_no_join_group(self):
        data = None
        for follow_group in d.wait_group_follow:
            if follow_group[1] == self:
                data = follow_group
                break
        if not data:
            return
        d.wait_group_follow.remove(data)
        return data[0]

    def answer_no_join_arena(self):
        data = None
        for follow_group in d.wait_arena_follow:
            if follow_group[1] == self:
                data = follow_group
                break
        if not data:
            return
        d.wait_arena_follow.remove(data)
        return data[0]

    def get_player_data(self):
        gm_user = self
        result = f"💰 Баланс: {gm_user.balance}\n💵 Доллары: {gm_user.dollars}\n🆙 Уровень: " \
                 f"{gm_user.lvl} ({gm_user.opit}/{100 + 100 * gm_user.lvl})\n⚡ Энергия: {gm_user.energy}\n" \
                 f"📈 Рейтинг: {gm_user.rating}"
        return result

    def get_group_player_from_number(self, message, cursor, connect):
        player = None
        number = d.EMOJI_NUMBER_ASSOTIATIONS[message]
        if number > 3 or number < 1:
            return
        data = None
        if self.group_id == 0:
            return
        group = Group([self], self.group_id, connect)
        if not group.group_id:
            self.group_id = 0
            return
        player_id = getattr(group, f'player{number}')
        player = player_connect(player_id, cursor)
        if not player:
            return
        return player

    def init_boss_fight(self, connect):
        cursor = connect.cursor()
        if not self.selected_boss:
            return d.ERROR
        boss = Boss(self.selected_boss, cursor)
        if not self.group_id:
            combat = Combat([self], [boss], d.COMBAT_TYPE_BOSS)
            combat.add_combat_to_combats()
            return d.SUCCESSFUL
        else:
            group = self.get_group_object(connect)
            for user in group:
                if user.energy < d.BOSS_FIGHT_PRICE:
                    return d.NEED_MORE_MONEY_ERROR
            if self.group_id in d.wait_boss_fight:
                return d.TIMEOUT_ERROR
            d.wait_boss_fight.update({self.group_id: [self.selected_boss, time.time()]})
            for user in group:
                user.fight_ready = False
                if user == self:
                    group.remove(user)
            self.fight_ready = True
            return [group, boss.user_name]

    def check_ready_boss_fight(self, connect):
        cursor = connect.cursor()
        if not self.group_id or not (self.group_id in d.wait_boss_fight):
            return
        self.fight_ready = True
        group = self.get_group_object(connect)
        _len = len(group)
        _iter = 0
        for user in group:
            if user.fight_ready:
                _iter += 1
        if _len == _iter:
            boss = Boss(d.wait_boss_fight[self.group_id][0], cursor)
            combat = Combat(group, [boss], d.COMBAT_TYPE_BOSS)
            combat.add_combat_to_combats()
            try:
                d.wait_boss_fight.pop(self.group_id)
            except KeyError:
                return
            return [group, True]
        group.remove(self)
        return [group, False]

    def add_item_to_database(self, proto_type, cursor, mods=0, new_id=False, flags=0):
        player = self
        count = 1
        if player.lastitem >= d.MAX_ITEMS:
            return None
        _id = (d.Global_Item_Id + 1)
        proto = proto_type[0]
        owner_id = self.user_id
        item_type = proto_type[1]
        try:
            d.ALL_TYPE_NAMES[item_type]
        except IndexError:
            return None
        # if d.START_RARE_ITEMS_PROTO > proto > d.LOOT_CASE_REWARD_TYPES[item_type]:
        #     return None
        iznos = 100
        if item_type in d.STACKABLE_TYPE and not new_id:
            count = proto_type[2] if len(proto_type) > 2 else count
            for item in player.items_obj:
                if item.proto_id == proto and item.type == item_type:
                    if check_flag(flags, d.ITEMS_FLAG_DAILY_BONUS) and item.count >= 3:
                        return None
                    item.update_param('count', item.count + count, cursor)
                    item.update_param('flags', item.flags | flags, cursor)
                    return item.id
        mods = mods if mods else 0
        bd_data = [
            _id,
            proto,
            item_type,
            iznos,
            mods,
            count,
            owner_id,
            flags
        ]
        d.Global_Item_Id += 1
        # result = "insert or ignore into items_param (id, proto_id, type, iznos, mods, count, owner_id, flags) values(" + "?," * (
        #         len(bd_data) - 1) + "?)"
        # cursor.execute(result, bd_data)
        result = "insert into items_param (id, proto_id, type, iznos, mods, count, owner_id, flags) values("
        for row in bd_data:
            result += f'{row},'
        result = result[:-1]
        result += ') ON CONFLICT DO NOTHING'
        cursor.execute(result)
        result = f"UPDATE items SET item{player.lastitem + 1} = {_id} Where user_id = {player.user_id}"
        cursor.execute(result)
        player.lastitem += 1
        # if not mods:
        self.items_obj.append(Item(d.Global_Item_Id, cursor))
        return d.Global_Item_Id
        # else:
        #     for i in mods:
        #         data = [_id]
        #         result = f"UPDATE items_param SET mods{i} = 1 Where item_id = ?"
        #         cursor.execute(result, data)
        #     self.items.append(d.Global_Item_Id)
        #     return d.Global_Item_Id

    # def add_st_item(self, proto_type, cursor):  # [прото без бонуса;номер типа;количество]
    #     return self.add_item_to_database(proto_type=proto_type, cursor=cursor)
    # proto_type = list(proto_type)
    # user_id = self.user_id
    # data_for_count = [user_id]
    # _count = proto_type[2]
    #
    # bonus_id = 0
    # for j in range(len(d.STACKABLE_TYPE)):
    #     if proto_type[1] == d.STACKABLE_TYPE[j]:
    #         bonus_id = d.BONUS_INTO_ID * j
    #         break
    # data = proto_type[0] + bonus_id
    # command = "SELECT * from items WHERE user_id = ?"
    # for row in cursor.execute(command, data_for_count):
    #     if row[data + d.MAX_ITEMS] is None:
    #         break
    #     if row[data + d.MAX_ITEMS] > 0:
    #         proto_type[2] += row[data + d.MAX_ITEMS]
    #         break
    # bd_data = [
    #     proto_type[2], user_id
    # ]
    # result = f"UPDATE items SET NS_item{data} = ? Where user_id = ?"
    # cursor.execute(result, bd_data)
    # if (proto_type[2] - _count) > 0:
    #     self.items.remove([proto_type[0] + bonus_id, proto_type[2] - _count])
    # self.items.append([proto_type[0] + bonus_id, proto_type[2]])
    # return [proto_type[0] + bonus_id, proto_type[2]]

    def loot_case_open(self, cursor, item):
        is_true = False
        # item = self.get_item_by_pid(proto, d.TYPE_LOOT_CASES_ID)
        if not item:
            return d.ERROR
        self.update_count_stack_item(cursor, item, -1)
        current_case = d.ALL_LOOT_CASES[item.proto_id]
        if current_case == d.LOOT_CASE_DEFAULT and d.GAME_RANDOM.Random(1, 10) < 8:
            money = d.GAME_RANDOM.Random(300, 1000)
            self.update_user_balance(cursor, money)
            result = f'✅ Вам выпало {money}💰'
            return result
        reward_type = d.GAME_RANDOM.Random(0, len(current_case[2]) - 1)
        reward_type = current_case[2][reward_type]
        reward_proto = d.GAME_RANDOM.Random(1, d.LOOT_CASE_REWARD_TYPES[reward_type])
        self.add_item_to_database(cursor=cursor, proto_type=[reward_proto, reward_type])
        result = f'✅ Вам выпал предмет: {get_item_name_proto(cursor, reward_proto, reward_type)}'
        return result

    def loot_case_buy(self, cursor, case):
        if case[1] > self.balance:
            return d.ERROR
        self.update_user_balance(cursor, -case[1])
        self.add_item_to_database(proto_type=[d.LOOT_CASE_DEFAULT[0], d.TYPE_LOOT_CASES_ID, 1], cursor=cursor)
        return d.SUCCESSFUL

    def show_all_player_params(self):
        string = f'🏧 Премиум = {self.premium}\n' \
                 f'🗺 Локация = {d.KEYBOARD_LOCATIONS[self.location][2:]}\n' \
                 f'💰 Баланс = {self.balance}\n' \
                 f'💵 Доллары = {self.dollars}\n' \
                 f'🆙 Уровень = {self.lvl}\n' \
                 f'🆙 Опыт = {self.opit}\n' \
                 f'⚡ Энергия = {self.energy}\n' \
                 f'🏆 Рейтинг Арены = {self.rating}\n' \
                 f'📈 Рейтинг Предметов = {self.items_rating}\n' \
                 f'🔪 Урон = {self.damage}\n' \
                 f'💀 Тип урона = {d.DAMAGE_TYPES[self.damage_type]}\n' \
                 f'🎲 Шанс на крит = {self.crit_chance}\n' \
                 f'🎲 Шанс попадания = {self.chance_to_hit}\n' \
                 f'💢 Пробивание = {self.penetrate}\n' \
                 f'❣ Здоровье = {self.max_hp}\n' \
                 f'🛡 Броня = {self.armor}\n' \
                 f'⚡ Защита от электро = {self.emp}\n' \
                 f'👊 Защита от удара = {self.punch}\n' \
                 f'💢 Защита от разрыва = {self.razriv}\n' \
                 f'☢ Защита от радиации = {self.radiation}\n' \
                 f'☣ Защита от химических ожогов = {self.chemical_burn}\n' \
                 f'💥 Защита от взрыва = {self.blast}\n' \
                 f'🔫 Защита от нормы = {self.shot}\n' \
                 f'❤ Регенерация = {self.regen}\n' \
                 f'🎲 Уворот = {self.dodge}\n'
        return string

    def end_mini_game(self):
        self.temp_data = []
        self.last_edit_message = None

    def count_rewards_mini_game2(self):
        if self.temp_data[0] != d.TEMP_MINI_GAME2_INDEX:
            return 0
        rows = self.temp_data[1]  # количество линий
        bet = self.temp_data[2]  # ставка
        game_str = self.temp_data[3]  # номер хода, начинается с 0
        # temp_val = bet
        # if len(self.temp_data) < 6:
        #     self.temp_data.append(bet)
        # self.temp_data[5] = int((self.temp_data[5]/(1-1/rows)-bet)*min(game_str, 1) + bet)
        # for i in range(game_str):
        #     temp_val = int((temp_val/(1-1/rows)-bet) + bet)
        return int(bet / (((rows - 1) / rows) ** game_str))

    def get_bin_data(self, bin_type):
        if bin_type == d.BIN_TYPE_EVENTS:
            value = d.PLAYER_EVENTS
            param = self.events
        elif bin_type == d.BIN_TYPE_SKINS:
            value = d.PLAYER_SKINS
            param = self.skins
        elif bin_type == d.BIN_TYPE_BACKGROUNDS:
            value = d.PLAYER_BACKGROUNDS
            param = self.backgrounds
        else:
            print('bin_data_err')
            return
        return [value, param]

    def add_bin_param(self, cursor, val, bin_type):
        if val > 31 or val < 0:
            return None
        data = self.get_bin_data(bin_type)
        self.update_database_value(cursor, data[0], data[1] | get_bin_param(val))

    def remove_bin_param(self, cursor, val, bin_type):
        if val > 31 or val < 0:
            return None
        data = self.get_bin_data(bin_type)
        self.update_database_value(cursor, data[0], data[1] & (get_bin_param(val) ^ 0xffffffff))

    def check_bin_param(self, val, bin_type):
        if val > 31 or val < 0:
            return None
        data = self.get_bin_data(bin_type)
        return data[1] & get_bin_param(val)

    def get_player_skins(self, cursor, bg=False):
        if not bg:
            text = '🎭 Выбери скин\n1) 😎 Стандартный\n'
            keyb_num = d.KEYBOARD_SKINS[0]
            check_type = d.BIN_TYPE_SKINS
            table = 'skins'
            name = 'skin_id'
        else:
            text = '🗺 Выбери фон\n1) 🏠 Стандартный\n'
            keyb_num = d.KEYBOARD_BACKGROUNDS[0]
            check_type = d.BIN_TYPE_BACKGROUNDS
            table = 'background'
            name = 'background_id'
        keyboard = VkKeyboard(inline=True)
        keyboard.add_button('1', color='secondary',
                            payload=(keyb_num * 100))
        _num = 2
        for i in range(1, 33):
            if _num == 11:
                return
            if self.check_bin_param(i, check_type):
                if _num == 6:
                    keyboard.add_line()
                cursor.execute(f'SELECT name from {table} WHERE {name} = {i}')
                _name = cursor.fetchall()[0][0]
                text += f'{_num}) {_name}\n'
                keyboard.add_button(f'{_num}', color='secondary',
                                    payload=(keyb_num * 100 + i))
                _num += 1
        text = text.replace('_', ' ')
        return [text, keyboard.get_keyboard()]

    def get_item_obj(self, item_id):  # ниже тестовые функции, идёт рефакторинг
        for item in self.items_obj:
            if item.id == item_id:
                return item

    def get_item_by_pid(self, item_pid, item_type):  # возвращает первый найденный итем в инвентаре игрока
        for item in self.items_obj:
            if item.proto_id == item_pid and item.type == item_type:
                return item

    def get_items_by_pid(self, item_pid):
        items = []
        for item in self.items_obj:
            if item.proto_id == item_pid:
                items.append(item)
        return items

    def remove_item_obj(self, item_id):
        for item in self.items_obj:
            if item.id == item_id:
                self.items_obj.remove(item)

    def use_item(self, item, cursor):
        if not item.is_can_use() or item.count < 1:
            self.send_message(f'❌ Предмет не подходит для использования')
            self.selected_item = None
            return
        if item.proto_id == 1:  # энергетик
            self.update_count_stack_item(cursor, item, -1, True)
            self.update_database_value(cursor, d.PLAYER_ENERGY, min(100, self.energy + 50))
            self.send_message(f'⚡ Энергия восстановлена до {self.energy} единиц')

    # def src_name(self):
    #     return f'[id{self.user_id}|{self.user_name}]'


def clear_old_data():  # работает в потоке
    start_time = time.time()
    while True:
        current_time = time.time()
        if current_time - start_time > d.ONE_MINUTE:
            start_time = current_time

            # удаление приглашений в группу каждые 20 минут
            for follow_group in d.wait_group_follow.copy():
                if current_time - follow_group[2] > d.TIME_TO_ERASE_PLAYER:
                    d.wait_group_follow.remove(follow_group)

            for follow_group in d.wait_arena_follow.copy():
                if current_time - follow_group[2] > d.TIME_TO_ERASE_PLAYER:
                    d.wait_arena_follow.remove(follow_group)

            # удаление игроков из списка активных
            try:
                for x in range(len(d.player_objects.copy())):
                    if current_time - d.player_objects[x].connect_time >= d.TIME_TO_ERASE_PLAYER:
                        d.active_users.remove(d.player_objects[x].user_id)
                        del d.player_objects[x]
            except IndexError:
                pass

            # удаление очереди к боссу
            for i in dict(d.wait_boss_fight):
                if current_time - d.wait_boss_fight[i][1] >= d.TIME_TO_ERASE_PLAYER:
                    try:
                        d.wait_boss_fight.pop(i)
                    except KeyError:
                        continue
        else:
            time.sleep(d.ONE_MINUTE - (current_time - start_time))
            continue


def wait_arena_process(connect):  # работает в потоке
    # connect = sqlite3.connect('BotStalker.db')
    cursor = connect.cursor()
    start_time = time.time()
    players = []
    while True:
        current_time = time.time()
        if len(d.wait_arena_fight) < 2:
            time.sleep(d.WAIT_EMPTY_DATA)
            continue
        if current_time - start_time > d.ONE_MINUTE:
            players.clear()
            start_time = current_time
            sorted_tuples = sorted(d.wait_arena_fight.items(), key=operator.itemgetter(1))
            sorted_dict = {k: v for k, v in sorted_tuples}
            for i in sorted_dict:
                players.append(i)
            for i in range(0, len(players), 2):
                player_id = players[i]
                opponent_id = players[i + 1]
                player = player_connect(player_id, cursor)
                opponent = player_connect(opponent_id, cursor)
                try:
                    if not player:
                        d.wait_arena_fight.pop(player_id)
                        continue
                    if not opponent:
                        d.wait_arena_fight.pop(opponent_id)
                        continue
                except KeyError:
                    continue
                combat = Combat([player], [opponent], d.COMBAT_TYPE_ARENA)
                combat.add_combat_to_combats()
                try:
                    d.wait_arena_fight.pop(player_id)
                    d.wait_arena_fight.pop(opponent_id)
                except KeyError:
                    continue
        else:
            time.sleep(d.ONE_MINUTE - (current_time - start_time))
            continue


def donut_process(connect):  # потоковая, обрабатывает донатики
    start_time = time.time()
    cursor = connect.cursor()
    keksik_api = KeksikApi(int(d.DONUT_GROUP_ID), d.DONUT_TOKEN)
    while True:
        current_time = time.time()
        if current_time - start_time > (d.ONE_MINUTE + 10):  # выполняется раз в 70 секунд
            start_time = current_time
            try:
                don = keksik_api.donates.getLast(str(d.LAST_DONUT_ID))
            except Exception as e:
                keksik_api = KeksikApi(int(d.DONUT_GROUP_ID), d.DONUT_TOKEN)
                time.sleep(30)
                continue
            if not don:
                return
            for don_data in don:
                if don_data.status != 'hidden' and don_data.op:
                    op = int(don_data.op)
                    for donut in d.DONUT_ALL:
                        if donut[0] == op and donut[1] <= int(don_data.amount):
                            player = player_connect(int(don_data.user), cursor)
                            if op == d.DONUT_PREMIUM[0]:
                                player.update_database_value(cursor, d.PLAYER_PREMIUM, 1)
                                player.send_message('✅ Премиум активирован!')
                            elif op == d.DONUT_TEST[0]:
                                player.send_message('✅ Тест!')
                keksik_api.donates.changeStatus(don_data.id, 'hidden')
            d.LAST_DONUT_ID = int(don[len(don)-1].id)
            cursor.execute(f"Update game_data SET last_donut = {d.LAST_DONUT_ID} Where item_id = 1")
            connect.commit()
        else:
            time.sleep(d.ONE_MINUTE + 10 - (current_time - start_time))
            continue
    pass


def messages_process(connect):
    start_time = time.time()
    cursor = connect.cursor()
    while True:
        current_time = time.time()
        if current_time - start_time > 0.4:
            start_time = current_time
            lst_msg = []
            lst_err = []
            for i in range(min(25, d.MESSAGES_QUEUE.qsize())):
                msg_data = d.MESSAGES_QUEUE.get()
                lst_msg.append(msg_data)
                lst_err.append(d.MSG_POOL.method(msg_data[0], {k:v for k, v in msg_data[1].items() if v is not None}))
            d.MSG_POOL.execute()
            abc = 0
            for msg in lst_msg:
                try:
                    if msg[0] == 'messages.send':
                        if not callable(lst_err[abc].result):
                            player = player_connect(msg[2], cursor)
                            player.last_edit_message = lst_err[abc].result
                    elif msg[0] == 'users.get':
                        if not callable(lst_err[abc].result):
                            _id = lst_err[abc].result
                            player = player_connect(msg[2], cursor)
                            is_arena = msg[3]
                            _id = _id[0]['id']
                            if player.user_id == _id:
                                player.send_message('❌ Нельзя приглашать самого себя')
                                continue
                            data = player.follow_user_to_group(_id, cursor, is_arena)
                            if data == d.NEED_MORE_MONEY_ERROR:
                                player.send_message('❌ У приглашённого игрока недостаточно энергии для арены')
                                continue
                            if data == d.PLAYER_NOT_FOUND_ERROR:
                                player.send_message('❌ Этот пользователь не зарегистрирован в игре')
                                continue
                            elif data == d.ERROR:
                                err_ans = 'сражается на арене' if is_arena else 'состоит в команде'
                                player.send_message(f'❌ Этот пользователь уже {err_ans} или приглашен другим игроком')
                                continue
                            elif data == d.SLOT_IS_BUSY_ERROR:
                                player.send_message(f'❌ Сначала ответь на последнее приглашение')
                                continue
                            elif data == d.NO_STACK_ERROR:
                                player.send_message(f'❌ Ты уже пригласил другого игрока, подожди ответа')
                                continue
                            inl_ans = 'на арену' if is_arena else 'в команду'
                            err = data.inline_keyboard(f'❓ Игрок {player.src_name} пригласил тебя '
                                                        f'{inl_ans}',
                                                  d.KEYBOARD_ARENA_WAIT_FOLLOW_ANSWER if is_arena else d.KEYBOARD_GROUP_WAIT_FOLLOW_ANSWER)
                            if err == d.MESSAGE_SEND_ERROR:
                                player.send_message('❌ Этот пользователь запретил отправлять ему сообщения')
                                continue
                            player.send_message(f'♻ Ты отправил приглашение игроку {data.src_name}')
                            continue
                    elif msg[0] == 'utils.getShortLink':
                        if not callable(lst_err[abc].result):
                            ref_string = lst_err[abc].result
                            ref_string = ref_string['short_url']
                            player = player_connect(msg[2], cursor)
                            player.update_database_value(cursor, d.PLAYER_REF_SRC, ref_string)
                            player.send_message(
                                      f'🗺 На кордоне есть торговец по имени Сидорович 👴. Он заинтересован в том, чтобы в Зону '
                                      f'приходили новые сталкеры 👶. Распространяй информацию о Зоне с помощью этой ссылки {ref_string} '
                                      f' 🌎. За каждого нового сталкера Сидорович заплатит тебе {d.SIDOROVICH_BONUS}💰',
                                      attachment=d.SIDOROVICH_PICTURE)
                except exceptions.VkRequestsPoolException as e:
                    print(e.args)
                    print(e.error)
                abc += 1
        else:
            time.sleep(0.4 - (current_time - start_time))

def time_events(connect):  # потоковая, отвечает за ежедневные бонусы и восстановление энергии
    events_game_tick = time.time()
    # connect = sqlite3.connect('BotStalker.db')
    cursor = connect.cursor()
    while True:
        current_time = time.time()
        if d.FIRST_HUNTING_GEN or current_time - d.HUNTING_TIME > 3600:
            d.HUNTING_TIME = current_time
            d.FIRST_HUNTING_GEN = False
            cr = Boss(500, cursor)
            cr.max_hp = cr.max_hp * d.GAME_RANDOM.Random(10, 30) // 10
            cr.armor = cr.armor * d.GAME_RANDOM.Random(10, 30) // 10
            cr.damage = cr.damage * d.GAME_RANDOM.Random(10, 30) // 10
            cr.dodge = cr.dodge * d.GAME_RANDOM.Random(10, 30) // 10
            cr.chance_to_hit = cr.chance_to_hit * d.GAME_RANDOM.Random(10, 20) // 10
            cr.crit_chance = cr.crit_chance * d.GAME_RANDOM.Random(10, 30) // 10
            cr.damage_type = d.GAME_RANDOM.Random(0, 6)
            cr.regen = cr.regen * d.GAME_RANDOM.Random(10, 30) // 10
            with open("bigText/names.txt") as inp:
                lines = inp.readlines()
            cr.user_name = choice(lines).strip()[:-1]
            cr.src_name = cr.user_name
            cr.source = choice(d.MINI_BOSSES_SOURCE_LIST).strip()
            cr.filename = None
            cr.is_mini_boss = True
            cr.reward = [(d.GAME_RANDOM.Random(200, 700), 500)]
            d.MINI_BOSS_OBJECT = cr
            cursor.execute(f'UPDATE users SET bar = 0')
            for player in d.player_objects:
                player.bar = 0
        # d.EVENTS_GAME_TICK = 5
        if current_time - events_game_tick < d.EVENTS_GAME_TICK:
            time.sleep(d.EVENTS_GAME_TICK - (current_time - events_game_tick))
            continue
        events_game_tick = current_time
        cursor.execute(f'SELECT user_id from users Where (energy = 99) or (energy = 98 and premium = 1)')
        all_energy_users = cursor.fetchall()
        if all_energy_users:
            for player_id in all_energy_users[0]:
                player = player_connect(player_id, cursor)
                player.send_message('⚡ Твоя энергия полностью восстановилась')
        cursor.execute(f'UPDATE users SET energy = energy + 1 WHERE energy < 100')
        cursor.execute(f'UPDATE users SET energy = energy + 1 WHERE (premium = 1 and energy < 100)')
        for player in d.player_objects:
            if player.premium:
                player.update_database_value(cursor, d.PLAYER_ENERGY, min(100, player.energy + 2))
            else:
                player.update_database_value(cursor, d.PLAYER_ENERGY, min(100, player.energy + 1))
        now = datetime.datetime.now()
        if now.hour == 21 and now.minute <= 6 and d.LAST_BONUS_DAY != now.date():
            cursor.execute(f'SELECT user_id FROM users')
            players = cursor.fetchall()
            for i in range(len(players)):
                id_ = int(players[i][0])
                player = player_connect(id_, cursor)
                res = player.add_item_to_database(cursor=cursor,
                                                  proto_type=[d.LOOT_CASE_DEFAULT[0], d.TYPE_LOOT_CASES_ID, 1],
                                                  flags=get_bin_param(d.ITEMS_FLAG_DAILY_BONUS))
                if res:
                    player.send_message(f'🎁 {player.src_name} получил ежедневный бонус - луткейс')
            d.LAST_BONUS_DAY = now.date()
            # data = cursor.execute(
            #     f'SELECT (id,flags) FROM items_param WHERE count < 3 OR count IS NULL').fetchall()
            # for flags in data:
            #     if check_flag(flags[1], d.ITEMS_FLAG_DAILY_BONUS):
            #         cursor.execute(f'UPDATE items_param SET count = count + 1 WHERE id = {flags[0]}')
            # players = cursor.fetchall()
            # for i in range(len(players)):
            #     id_ = int(players[i][0])
            #     player = player_connect(id_, cursor)
            #     player.add_st_item(cursor=cursor, proto_type=[d.LOOT_CASE_DEFAULT[0], d.TYPE_LOOT_CASES_ID, 1])
            #     player.send_message(f'🎁 {player.src_name} получил ежедневный бонус - луткейс')
            #     d.LAST_BONUS_DAY = now.date()
        connect.commit()


# def events_test(cursor):
#     now = datetime.datetime.now()
#     d.LAST_BONUS_DAY = now.date()
#     print(type(now.date()))
#     # cursor.execute(f'UPDATE users SET energy = energy + 1 WHERE energy < 100')


def sidorovich_reward(user_id, refer_id, cursor):
    if not refer_id.isdecimal():
        return
    refer_id = int(refer_id)
    if not (check_valid_player_id(refer_id, cursor)):
        return
    player = player_connect(refer_id, cursor)
    player.update_user_balance(cursor, d.SIDOROVICH_BONUS)
    player.send_message(
        f'👤 Пользователь https://vk.com/id{user_id} перешёл по ссылке. Сидорович передал тебе {d.SIDOROVICH_BONUS}💰')


class Boss:
    def __init__(self, boss_id, cursor):
        self.user_id = boss_id
        self.user_name = ''
        self.damage_type = 0
        self.damage = 0
        self.crit_chance = 0
        self.chance_to_hit = 0
        self.armor = 0
        self.emp = 0
        self.punch = 0
        self.razriv = 0
        self.radiation = 0
        self.chemical_burn = 0
        self.blast = 0
        self.shot = 0
        self.regen = 0
        self.max_hp = 0
        self.current_hp = 0
        self.dodge = 0
        self.penetrate = 0
        self.source = ''
        self.filename = ''
        self.is_player = False
        self.is_mini_boss = False
        self.skills = 0  # всегда ноль
        self.current_skill = 0  # всегда ноль
        self.side = 0  # 1 - лево, 2 - право
        self.target = None  # для боёвки
        self.reward = d.ALL_BOSSES_REWARD[boss_id]  # трофеи за победу, только для боссов
        self.lvl = 0  # всегда ноль
        self.stat_parse(cursor)
        self.user_name = self.user_name.replace('_', ' ')
        self.src_name = self.user_name

    def stat_parse(self, cursor):
        string = "SELECT * from bosses WHERE user_id = " + str(self.user_id)
        cursor.execute(string)
        res = cursor.fetchall()
        for row in res:
            if row[0] == self.user_id:
                for i in d.ALL_BOSS_PARAMS:
                    setattr(self, i[1], row[i[0]])
        self.current_hp = self.max_hp


class Combat:
    def __init__(self, left_critters, right_critters, combat_type, add_rating=True):
        self.left_critters = left_critters
        self.right_critters = right_critters
        self.current_turn = 0
        self.combat_type = combat_type
        self.events = []  # формат: [тип, таргет, количество ходов, чо-нибудь]
        self.add_rating = add_rating

    def get_all_critters(self):
        critters = self.left_critters + self.right_critters
        return critters

    def return_hp(self):  # приравнивает текущие хп всех участников боя к максимальным
        critters = self.get_all_critters()
        for critter in critters:
            critter.current_hp = critter.max_hp

    def add_combat_to_combats(self):
        critters = self.get_all_critters()
        if self.right_critters[0].user_id == 22:  # бойцы монолита
            boss = self.right_critters[0]
            # boss.src_name = 'Боец монолита'
            boss2 = deepcopy(boss)
            boss3 = deepcopy(boss)
            boss.src_name = 'Харон'
            boss2.src_name = 'Проповедник'
            boss3.src_name = 'Молитвенник'
            self.right_critters = [boss, boss2, boss3]
        for critter in critters:
            if critter.is_player:
                critter.is_busy = True
                critter.last_edit_message = 0
        d.combat_objects.append(self)

    def remove_combat_from_combats(self):
        critters = self.get_all_critters()
        for critter in critters:
            if critter.is_player:
                critter.is_busy = False
                critter.last_edit_message = 0
                critter.current_skill = 0
                critter.skills_cd = 0
                critter.keyboard = d.KEYBOARD_MAIN
        d.combat_objects.remove(self)
        cancel_all_events(self)


def check_combat_die(critters):
    die = 0
    for critter in critters:
        if critter.current_hp <= 0:
            die += 1
    if die == len(critters):
        return 1
    else:
        return 0


def combat_boss_rewards(loose_party):
    reward = []
    for boss in loose_party:
        if boss.is_player:
            continue
        reward.append(boss.reward)
        return reward  # награда выдаётся только за одного из боссов, чтобы не было слишком жирно


def add_iznos(critter, cursor, connect):
    _item_list = [critter.left_hand, critter.right_hand, critter.active_armor, critter.helmet]
    _names = ["left_hand", "right_hand", "active_armor", "helmet"]
    for _i in range(len(_item_list)):
        breaking = d.GAME_RANDOM.Random(0, 5)
        cursor.execute(f"Select iznos from items_param WHERE id = {_item_list[_i]}")
        cur_iznos = cursor.fetchall()
        if not cur_iznos:
            continue
        cur_iznos = cur_iznos[0][0]
        _res = max(cur_iznos - breaking, 0)
        cursor.execute(f"UPDATE items_param SET iznos = {_res} WHERE id = {_item_list[_i]}")
        if _res == 0:
            critter.move_item_from_skin(cursor, connect, [0, _names[_i]])
            critter.send_message(f'🛠 Один из ваших предметов сломался и был перенесён в инвентарь')
    pass


def combat_result(combat, winner, cursor, connect):
    winner_party = combat.left_critters if winner == d.COMBAT_LEFT_SIDE else combat.right_critters
    loose_party = combat.right_critters if winner == d.COMBAT_LEFT_SIDE else combat.left_critters
    opit = 0
    rating = 0
    rewards = combat_boss_rewards(loose_party) if combat.combat_type == d.COMBAT_TYPE_BOSS else None
    for critter in loose_party:
        opit += critter.max_hp
        rating += critter.lvl
        if critter.is_player:
            critter.update_database_value(cursor, d.PLAYER_ENERGY, max(0, critter.energy - (
                d.BOSS_FIGHT_PRICE if combat.combat_type == d.COMBAT_TYPE_BOSS else d.ARENA_FIGHT_PRICE)))
            add_iznos(critter, cursor, connect)
            critter.send_message(f'🆚 {critter.src_name} проиграл.')
    for player in winner_party:
        result = f'💯 Игрок {player.src_name} победил.\n➕ Получено опыта: {opit}.\n'
        if not player.is_player:
            continue
        player.update_database_value(cursor, d.PLAYER_ENERGY, max(0, player.energy - (
            d.BOSS_FIGHT_PRICE if combat.combat_type == d.COMBAT_TYPE_BOSS else d.ARENA_FIGHT_PRICE)))
        add_iznos(player, cursor, connect)
        player.opit += (opit * 2) if player.premium else opit
        player.check_lvl_up(cursor)
        if combat.combat_type == d.COMBAT_TYPE_BOSS:
            rare = False
            result += '🎁 Получены предметы: '
            for reward in rewards:
                for reward_part in reward:
                    if reward_part[1] == d.MINI_BOSS_REWARD:
                        player.update_user_balance(cursor, reward_part[0])
                        result += f'{reward_part[0]}💰, '
                    elif reward_part[1] == d.TYPE_REWARDS_SKIN:
                        if not player.check_bin_param(reward_part[0], d.BIN_TYPE_SKINS):
                            player.add_bin_param(cursor, reward_part[0], d.BIN_TYPE_SKINS)
                            result += f'Скин {reward_part[2]}, '
                    elif reward_part[1] == d.TYPE_REWARDS_BACKGROUND:
                        if not player.check_bin_param(reward_part[0], d.BIN_TYPE_BACKGROUNDS):
                            player.add_bin_param(cursor, reward_part[0], d.BIN_TYPE_BACKGROUNDS)
                            result += f'Фон {reward_part[2]}, '
                    else:
                        check_rare_item = reward_part[0] > d.BONUS_INTO_ID / 2 if reward_part[1] in d.STACKABLE_TYPE else reward_part[0] > d.START_RARE_ITEMS_PROTO
                        if check_rare_item:
                            if rare:
                                continue
                            if d.GAME_RANDOM.Random(1, 100) > 5:
                                continue  # проверка на редкие предметы, шанс выпадения 1/20
                            else:
                                rare = True
                        if reward_part[1] == d.TYPE_LOOT_CASES_ID:
                            if d.GAME_RANDOM.Random(1, 10) > 3:  # шанс на выпадение кейса 30%
                                continue
                        temp = player.add_item_to_database(proto_type=reward_part, cursor=cursor)
                        if not temp:
                            print('Ошибка выдачи награды за босса', reward_part)
                            continue
                        result += player.get_item_obj(temp).name + ', '
            result = result[:-2]
        elif combat.combat_type == d.COMBAT_TYPE_ARENA:
            sub_str = f'Заработано рейтинга: {rating} 🏆' if combat.add_rating else ''
            result += f'Заработано денег: {d.ARENA_REWARD}💰.\n{sub_str}'
            player.balance += d.ARENA_REWARD
            if (player not in d.ADMINISTRATORS) and combat.add_rating:
                player.rating += rating
            player.update_database_value(cursor, d.PLAYER_BALANCE, player.balance)
            player.update_database_value(cursor, d.PLAYER_RATING, player.rating)
        player.send_message(result, attachment=d.ARENA_WIN_PICTURE)
    combat.return_hp()
    combat.remove_combat_from_combats()


def get_live_critters(critters):
    result = []
    for critter in critters:
        if critter.current_hp > 0:
            result.append(critter)
    return result


def first_turn(combat):
    combat_type = combat.combat_type
    if combat_type == d.COMBAT_TYPE_BOSS:
        current_boss = combat.right_critters[0]
        text = f'🐲 Начался бой с боссом {current_boss.user_name}'
        for player in combat.left_critters:
            if not player.is_player:
                continue
            player.send_message(text, attachment=current_boss.filename)
            if player.peer_id:
                if len(combat.left_critters) == 3 and combat.left_critters[0].peer_id == combat.left_critters[
                    1].peer_id == \
                        combat.left_critters[2].peer_id:
                    break
                elif len(combat.left_critters) == 2 and combat.left_critters[0].peer_id == combat.left_critters[
                    1].peer_id:
                    break
    elif combat_type == d.COMBAT_TYPE_ARENA:
        if len(combat.left_critters) == 1 and len(combat.right_critters) == 1:
            l_player = combat.left_critters[0]
            r_player = combat.right_critters[0]
            l_player.target = r_player
            r_player.target = l_player
            players = [l_player, r_player]
            for player in players:
                target = player.target
                text = f'⚔ Начался бой с игроком {target.src_name}. Характеристики противника:\n' \
                       f'🆙 Уровень: {target.lvl}\n❣ Здоровье: {target.max_hp}\n' \
                       f'🔪 Урон: {target.damage}\n💢 Пробивание: {target.penetrate}\n🛡 Защита: {target.armor}\n' \
                       f'💉 Регенерация: {target.regen}\n🎲 Шанс на крит: {target.crit_chance}\n' \
                       f'🎲 Шанс попадания: {target.chance_to_hit}\n🎲 Уворот: {target.dodge}\n' \
                       f'{d.DAMAGE_TYPES_EMOJI[player.damage_type]} Защита от {d.DAMAGE_TYPES[player.damage_type]}: ' \
                       f'{getattr(target, d.DAMAGE_TYPES_DB_NAME[player.damage_type])}\n' \
                       f'{d.DAMAGE_TYPES_EMOJI[target.damage_type]} Тип урона: {d.DAMAGE_TYPES[target.damage_type]}\n'
                player.send_message(text, attachment='video-210036099_456239018')


def combat_no_winners(combat):
    critters = combat.get_all_critters()
    for player in critters:
        if player.is_player:
            player.send_message(f'⌛ Превышен лимит ходов: {d.COMBAT_LAST_TURN}, бой окончен')


def check_events(combat):
    for i in range(len(combat.events)):
        if not (combat.events[i][2] <= 1):
            combat.events[i][2] -= 1
            continue
        event_type = combat.events[i][0]
        event_target = combat.events[i][1]
        event_param = combat.events[i][3]
        combat.events[i] = None
        if event_type == d.EVENT_BOMB:
            event_target.armor = int(event_target.armor * 1.25)
        elif event_type == d.EVENT_HEAD_SHOT:
            event_target.crit_chance = event_param[0]
            event_target.chance_to_hit = event_param[1]
        elif event_type == d.EVENT_TANK:
            event_target.armor = int(event_target.armor * 0.8)
    while None in combat.events:
        combat.events.remove(None)


def cancel_all_events(combat):
    for i in range(len(combat.events)):
        combat.events[i][2] = 1
    check_events(combat)


def combat_process(connect):  # работает в потоке
    combat_game_tick = time.time()
    # connect = sqlite3.connect('BotStalker.db')
    cursor = connect.cursor()
    while True:
        current_time = time.time()
        if not d.combat_objects:
            time.sleep(d.COMBAT_GAME_TICK)
            continue
        if current_time - combat_game_tick < d.COMBAT_GAME_TICK:
            time.sleep(d.COMBAT_GAME_TICK - (current_time - combat_game_tick))
            continue
        combat_game_tick = current_time
        for combat in d.combat_objects:
            if check_combat_die(combat.left_critters):
                combat_result(combat, d.COMBAT_RIGHT_SIDE, cursor, connect)
                connect.commit()
                continue
            elif check_combat_die(combat.right_critters):
                combat_result(combat, d.COMBAT_LEFT_SIDE, cursor, connect)
                connect.commit()
                continue
            if combat.current_turn == 0:  # начало боя________________________
                first_turn(combat)
                combat.current_turn += 1
                continue
            if combat.current_turn >= d.COMBAT_LAST_TURN:  # конец боя_____________________
                combat.remove_combat_from_combats()
                combat_no_winners(combat)

            live_left_critters = get_live_critters(combat.left_critters)
            live_right_critters = get_live_critters(combat.right_critters)
            result = '💥 Ход: ' + str(combat.current_turn) + '\n'
            for critter in combat.left_critters:
                critter.target = live_right_critters[d.GAME_RANDOM.Random(0, len(live_right_critters) - 1)]
                critter.side = d.COMBAT_LEFT_SIDE
            for critter in combat.right_critters:
                critter.target = live_left_critters[d.GAME_RANDOM.Random(0, len(live_left_critters) - 1)]
                critter.side = d.COMBAT_RIGHT_SIDE
            critters = combat.get_all_critters()

            check_events(combat)
            for critter in critters:
                if critter.current_hp <= 0:
                    continue
                if critter.is_player:
                    critter.skills_cd = max(0, critter.skills_cd - 1)
                target = critter.target
                if critter.side == target.side:
                    print('side error')
                    continue

                if not critter.is_player:  # способности боссов
                    if critter.user_id == 21:  # стрелок
                        if d.GAME_RANDOM.Random(1, 6) == 3:
                            critter.current_hp = min(critter.max_hp, critter.current_hp + 250)
                            result += f'🔮 {critter.src_name} использовал травы болотного доктора и восстановил часть здоровья ❤.\n'
                    elif critter.user_id == 23:  # черный сталкер
                        if d.GAME_RANDOM.Random(1, 6) == 4:
                            for player in combat.left_critters:
                                player.current_hp *= 0.66
                            result += f'🔮 {critter.src_name} призвал поле аномалий. Здоровье всех игроков уменьшилось 💔.\n'
                    elif critter.user_id == 17:  # псевдогигант
                        if d.GAME_RANDOM.Random(1, 5) == 5:
                            target.current_hp /= 2
                            result += f'🔮 {critter.src_name} использовал секретную атаку. Здоровье {target.src_name} значительно снизилось 💔.\n'

                if critter.current_skill and critter.skills >= critter.current_skill and critter.skills_cd <= 0:  # скиллы игрока_________
                    if d.ALL_SKILLS[critter.current_skill] == d.SKILL_GRENADE_THROW:
                        combat.events.append(
                            [d.EVENT_BOMB, target, 3, 0])  # формат: [тип, таргет, количество ходов, чо-нибудь]
                        target.armor = target.armor * 0.8
                        result += f'🔮 {critter.src_name} уменьшил защиту {target.src_name} до {int(target.armor)} на 3 хода 🛡.\n'
                        critter.skills_cd = 2
                        critter.current_skill = 0
                    elif d.ALL_SKILLS[critter.current_skill] == d.SKILL_HEAD_SHOT:
                        combat.events.append(
                            [d.EVENT_HEAD_SHOT, critter, 1, [critter.crit_chance, critter.chance_to_hit]])
                        critter.crit_chance = 100
                        critter.chance_to_hit = 200
                        critter.skills_cd = 3
                        result += f'🔮 {critter.src_name} Делает выстрел в голову.\n'
                    elif d.ALL_SKILLS[critter.current_skill] == d.SKILL_TANK:
                        combat.events.append(
                            [d.EVENT_TANK, critter, 3, [critter.armor]])
                        critter.armor *= 1.25
                        critter.skills_cd = 2
                        result += f'🔮 {critter.src_name} Занял укратие, его защита выросла до {int(critter.armor)} 🛡.\n'
                elif critter.current_skill and critter.skills >= critter.current_skill and critter.skills_cd > 0:
                    critter.send_message(f'🆒 Способности будут доступны через {critter.skills_cd} ходов')
                critter.current_skill = 0
                # боёвка начало
                blank_damage = d.GAME_RANDOM.Random(max(1, (critter.damage - target.armor) / 2),
                                                    max((critter.damage - target.armor),
                                                        2))  # рандомное число, если урон меньше защиты то разброс 1-2
                # множитель урона, минималка 0.1.
                damage_multiplier = max((100 - getattr(target,
                                                       d.DAMAGE_TYPES_DB_NAME[
                                                           critter.damage_type]) + critter.penetrate) * 0.01, 0.1)
                damage_multiplier = 1 if damage_multiplier > 1 else damage_multiplier
                critical_multiplier = 2 if (d.GAME_RANDOM.Random(1, 100) < max(min(critter.crit_chance, 95), 5)) else 1
                temp_ = d.GAME_RANDOM.Random(1, 100)
                hit = 1 if (temp_ < max(min((critter.chance_to_hit - target.dodge), 95), 5)) else 0
                damage = int(max(blank_damage * damage_multiplier * critical_multiplier, 1))  # итоговый урон, минимум 1
                damage *= hit  # если промах, то урон уменьшается до нуля
                critter.current_hp = int(min(critter.max_hp, critter.current_hp + critter.regen))
                target.current_hp = int(max(0, target.current_hp - damage))
                tmp_reten_str = f' и восстановил {critter.regen} здоровья 💉.' if critter.regen > 0 else '.'
                # боевка конец

                dmg_str = f'Нанёс {damage} урона по' if hit == 1 else f'Промахнулся при попытке атаковать'
                death_str = f'💀 {target.src_name} умирает.\n' if target.current_hp <= 0 else ''
                buffer = f'🤜 {critter.src_name} {dmg_str} {target.src_name}{tmp_reten_str}' \
                         f'\n❣ Здоровье {critter.src_name} = {critter.current_hp}, ' \
                         f'здоровье {target.src_name} = {target.current_hp}.\n{death_str}'
                result = result + buffer
            combat.current_turn += 1
            for player in critters:
                if not player.is_player:
                    continue
                user_msg = result + f'⭐ {player.src_name}, для применения навыков используй кнопки:'
                keyboard = VkKeyboard(inline=True)
                for i in range(1, player.skills + 1):
                    keyboard.add_callback_button(d.ALL_SKILLS_EMOJI[i], color='primary',
                                                 payload=(d.KEYBOARD_FIGHT_MAGIC[0] * d.PAYLOAD_MULTIPLIER + i))
                player.send_message(user_msg, keyb=keyboard.get_keyboard(), is_edit=True if combat.current_turn > 2 else False)
                # else:
                #     player.send_message(user_msg, is_edit=True)
