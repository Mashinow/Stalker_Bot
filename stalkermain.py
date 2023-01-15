import sqlite3
import psycopg2
import stalker
import defines as d
import vk_api
import time
import traceback
import sys
from copy import deepcopy
import mersen
import threading
import json
import send_mes
from requests import exceptions
# from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.bot_longpoll import VkBotEventType

"""
Главный файл бота. С него необходимо запускать проект, здесь же происходит чтение и обработка сообщений от пользователей
"""

token = d.TOKEN
d.GAME_RANDOM = mersen.Randomizer()
d.GAME_RANDOM.Generate(int(time.time()))
if d.SEND_EVENT:
    send_mes.go_send_mes()
connect = psycopg2.connect(dbname=d.DATABASE_INFO["dbname"], user=d.DATABASE_INFO["user"],
                        password=d.DATABASE_INFO["password"], host=d.DATABASE_INFO["host"])
cursor = connect.cursor()

cursor.execute("SELECT last_donut from game_data WHERE item_id = 1")
d.LAST_DONUT_ID = cursor.fetchall()[0][0]

start_time = time.time()
threading.Thread(target=stalker.combat_process, args=(connect,)).start()
threading.Thread(target=stalker.clear_old_data).start()
threading.Thread(target=stalker.wait_arena_process, args=(connect,)).start()
threading.Thread(target=stalker.time_events, args=(connect,)).start()
threading.Thread(target=stalker.messages_process, args=(connect,)).start()
if d.DONUT_WORK:
    threading.Thread(target=stalker.donut_process, args=(connect,)).start()

thrEvent = threading.Event()

cursor.execute('SELECT MAX(group_id) FROM groups')
d.Global_Group_Id = cursor.fetchall()[0][0]
if not d.Global_Group_Id:
    d.Global_Group_Id = 0

# for i2 in range(len(d.ALL_TYPE_NAMES)):
#     data2 = cursor.execute(f'PRAGMA table_info({d.ALL_TYPE_NAMES[i2]});').fetchall()
#     for j2 in data2:
#         d.PRAGMA_ALL[i2].append(j2[1])


for i2 in range(len(d.ALL_TYPE_NAMES)):
    cursor.execute(f'''SELECT
        column_name,
        ordinal_position
    FROM
        information_schema.columns
    WHERE
        table_name = '{d.ALL_TYPE_NAMES[i2]}';''')
    tmp = d.quicksort(cursor.fetchall())
    for j2 in tmp:
        d.PRAGMA_ALL[i2].append(j2[0])

# for ii in cursor.execute('SELECT * FROM items_param'):
cursor.execute('SELECT * FROM items_param')
tmp = cursor.fetchall()
for ii in tmp:
    d.Global_Item_Id = max(ii[0], d.Global_Item_Id)
# for ii in cursor.execute('SELECT * FROM groups'):
#     d.Global_Group_Id = max(ii[0], d.Global_Group_Id)

cursor.execute(f'SELECT * FROM {d.TYPE_ARMOR_NAME} WHERE item_id < {d.START_RARE_ITEMS_PROTO}')
for ii in cursor:
    d.LOOT_CASE_REWARD_TYPES[d.TYPE_ARMOR_ID] = max(ii[0], d.LOOT_CASE_REWARD_TYPES[d.TYPE_ARMOR_ID])
cursor.execute(f'SELECT * FROM {d.TYPE_ARTEFACTS_NAME} WHERE item_id < {d.START_RARE_ITEMS_PROTO}')
for ii in cursor:
    d.LOOT_CASE_REWARD_TYPES[d.TYPE_ARTEFACTS_ID] = max(ii[0], d.LOOT_CASE_REWARD_TYPES[d.TYPE_ARTEFACTS_ID])
cursor.execute(f'SELECT * FROM {d.TYPE_WEAPONS_NAME} WHERE item_id < {d.START_RARE_ITEMS_PROTO}')
for ii in cursor:
    d.LOOT_CASE_REWARD_TYPES[d.TYPE_WEAPONS_ID] = max(ii[0], d.LOOT_CASE_REWARD_TYPES[d.TYPE_WEAPONS_ID])
cursor.execute(f'SELECT * FROM {d.TYPE_HELMETS_NAME} WHERE item_id < {d.START_RARE_ITEMS_PROTO}')
for ii in cursor:
    d.LOOT_CASE_REWARD_TYPES[d.TYPE_HELMETS_ID] = max(ii[0], d.LOOT_CASE_REWARD_TYPES[d.TYPE_HELMETS_ID])
cursor.execute(f'SELECT * FROM {d.TYPE_UPGRADES_ARMOR_NAME} WHERE item_id < {d.BONUS_INTO_ID / 2}')
for ii in cursor:
    d.LOOT_CASE_REWARD_TYPES[d.TYPE_UPGRADES_ARMOR_ID] = max(ii[0], d.LOOT_CASE_REWARD_TYPES[d.TYPE_UPGRADES_ARMOR_ID])
cursor.execute(f'SELECT * FROM {d.TYPE_UPGRADES_WEAPON_NAME} WHERE item_id < {d.BONUS_INTO_ID / 2}')
for ii in cursor:
    d.LOOT_CASE_REWARD_TYPES[d.TYPE_UPGRADES_WEAPON_ID] = max(ii[0],
                                                              d.LOOT_CASE_REWARD_TYPES[d.TYPE_UPGRADES_WEAPON_ID])
cursor.execute(f'SELECT * FROM {d.TYPE_UPGRADES_HELMET_NAME} WHERE item_id < {d.BONUS_INTO_ID / 2}')
for ii in cursor:
    d.LOOT_CASE_REWARD_TYPES[d.TYPE_UPGRADES_HELMET_ID] = max(ii[0],
                                                              d.LOOT_CASE_REWARD_TYPES[d.TYPE_UPGRADES_HELMET_ID])


def fail_message(gm_user):
    blasthack(gm_user, d.DEFAULT_BOT_ANSWER)
    gm_user.keyboard = d.KEYBOARD_MAIN


def make_vk_image(art):
    try:
        upload = vk_api.VkUpload(d.GIVE)
    except json.decoder.JSONDecodeError:
        print('json.decoder.JSONDecodeError')
        return None
    try:
        photo = upload.photo_messages(art)
    except vk_api.exceptions.ApiError:
        return None
    except exceptions.ConnectionError:
        d.restart_connection()
        return None
    owner_id = photo[0]['owner_id']
    photo_id = photo[0]['id']
    access_key = photo[0]['access_key']
    attachment = f'photo{owner_id}_{photo_id}_{access_key}'
    return attachment
    # d.GIVE.messages.send(peer_id=(gm_user.peer_id if gm_user.peer_id != 0 else gm_user.id),
    #                    random_id=random.randint(0, 2048), attachment=attachment)


def get_button_number(key_num):
    if key_num and str(key_num).isdigit():
        return key_num % d.PAYLOAD_MULTIPLIER
    else:
        return -1


def check_valid_sum(gm_user, text, log=True):
    if text.isdigit():
        if 0 < int(text) < 0xffffffff:
            return int(text)
        else:
            if log:
                blasthack(gm_user, '❌ Вы ввели отрицательное число')
            return d.ERROR
    else:
        if log:
            blasthack(gm_user, '❌ Вы ввели не число')
        return d.ERROR


def check_bet(gm_user, message):
    if not message.isdigit():
        return '❌ Вы ввели не число'
    value = int(message)
    if not value > 0:
        return '❌ Вы ввели отрицательное число'
    if value > gm_user.balance:
        return '❌ Недостаточно денег'
    if value > 10000000:
        return '❌ Лимит ставки 10000000'
    return None


# def send_msg(gm_user, message, keyboard=None, attachment=None, template=None):
#     mess_id = None
#     try:
#         mess_id = d.GIVE.messages.send(peer_id=(gm_user.peer_id if gm_user.peer_id != 0 else gm_user.user_id),
#                                        message=message,
#                                        random_id=int(time.time() * 1000000),
#                                        keyboard=keyboard,
#                                        attachment=attachment,
#                                        template=template)
#     except vk_api.exceptions.ApiError:
#         if not gm_user.last_peer_id:
#             return d.MESSAGE_SEND_ERROR
#         try:
#             d.GIVE.messages.send(peer_id=gm_user.last_peer_id,
#                                  message=message,
#                                  random_id=int(time.time() * 1000000),
#                                  keyboard=keyboard,
#                                  attachment=attachment,
#                                  template=template
#                                  )
#         except vk_api.exceptions.ApiError:
#             return d.MESSAGE_SEND_ERROR
#     except exceptions.ConnectionError:
#         d.restart_connection()
#         return d.MESSAGE_SEND_ERROR
#     return mess_id


def blasthack(gm_user, text, image=None, is_edit=False):
    # message = text
    # keyboard = open(keyb, "r", encoding="UTF-8").read()
    if gm_user.send_message(text, d.BASE_KEYBOARD_DATA, image, is_edit=is_edit) == d.MESSAGE_SEND_ERROR:
        return d.MESSAGE_SEND_ERROR


def inline_keyboard(gm_user, text, answers_list, image=None, is_edit=False, is_callback=False):
    return gm_user.inline_keyboard(text, answers_list, image, is_edit, is_callback)


def inline_keyboard_specifik(gm_user, text, answers_list, flag, image=None, is_edit=False):
    keyboard = VkKeyboard(inline=True)
    msg_len = len(answers_list) - 1
    for i in range(1, len(answers_list)):
        keyboard.add_button(answers_list[i], color=VkKeyboardColor.PRIMARY,
                            payload=f'{answers_list[0] * d.PAYLOAD_MULTIPLIER + i - 1}')
        if flag == d.MESSAGE_FLAG_NO_LINE:
            continue
    message = text
    if gm_user.send_message(message, keyboard.get_keyboard(), image, is_edit=is_edit) == d.MESSAGE_SEND_ERROR:
        return d.MESSAGE_SEND_ERROR
    gm_user.keyboard = answers_list[0]


def numbers_keyboard(gm_user, text, start, end, text_data=None, is_edit=False, key_num=0):
    if text_data is None:
        text_data = []
    keyboard = VkKeyboard(inline=True)
    for i in range(max(1, start), min(end + 1, 8)):
        keyboard.add_button(d.KEYBOARD_INVENTORY_ANSWERS[i],
                            color=(VkKeyboardColor.SECONDARY if text_data else VkKeyboardColor.PRIMARY), payload=key_num * d.PAYLOAD_MULTIPLIER if key_num else None)
        if i == 5 and min(end + 1, 8) > 6:
            keyboard.add_line()
    if text_data:
        keyboard.add_line()
        msg_len = len(text_data)
        for i in range(1, msg_len):
            keyboard.add_button(text_data[i], color=VkKeyboardColor.PRIMARY, payload=key_num * d.PAYLOAD_MULTIPLIER if key_num else None)
            if i < msg_len - 1:
                keyboard.add_line()
    message = text
    if gm_user.send_message(message, keyboard.get_keyboard(), is_edit=is_edit) == d.MESSAGE_SEND_ERROR:
        return d.MESSAGE_SEND_ERROR


def mini_game2_keyboard(gm_user):
    tmp_val = gm_user.temp_data
    if not tmp_val:
        return
    rows = tmp_val[1]  # количество линий
    bet = tmp_val[2]  # ставка
    game_str = tmp_val[3]  # номер хода, начинается с 0
    last_turns = tmp_val[
        4]  # вложенный список, вид  {0:[x,y], 1:[x,y]}, где x - бомба, y - ход игрока, число - номер хода
    zone_len = 5
    payload = d.PAYLOAD_MULTIPLIER  # если чот сломается будет мэйн клава
    is_loose = False
    keyb_num = d.KEYBOARD_MINI_GAME2_2[0]
    keyboard = VkKeyboard(inline=False)
    for i in range(rows):
        for j in range(zone_len):
            payload = keyb_num * d.PAYLOAD_MULTIPLIER + j + i * 5
            if j == game_str:
                keyboard.add_callback_button('🚪', color=VkKeyboardColor.PRIMARY, payload=payload)
            elif j > game_str:
                keyboard.add_callback_button('&#8195;', color=VkKeyboardColor.SECONDARY, payload=payload)
            elif j < game_str:
                if last_turns[j][0] == last_turns[j][1] == i:
                    keyboard.add_callback_button('💀', color=VkKeyboardColor.NEGATIVE, payload=payload)
                    is_loose = True
                elif last_turns[j][0] == i:
                    keyboard.add_callback_button(d.DAMAGE_TYPES_EMOJI[2 + j], color=VkKeyboardColor.SECONDARY,
                                                 payload=payload)
                elif last_turns[j][1] == i and j == game_str - 1:
                    keyboard.add_callback_button('🕵', color=VkKeyboardColor.PRIMARY, payload=payload)
                elif last_turns[j][1] == i:
                    keyboard.add_callback_button('👣', color=VkKeyboardColor.PRIMARY, payload=payload)
                else:
                    keyboard.add_callback_button('&#8195;', color=VkKeyboardColor.SECONDARY, payload=payload)
        keyboard.add_line()
    keyboard.add_callback_button('💰 Забрать выигрыш', color=VkKeyboardColor.POSITIVE,
                                 payload=keyb_num * d.PAYLOAD_MULTIPLIER + 97)
    keyboard.add_line()
    keyboard.add_callback_button('🚪 Назад', color=VkKeyboardColor.NEGATIVE,
                                 payload=keyb_num * d.PAYLOAD_MULTIPLIER + 98)
    keyboard.add_callback_button('🌲 Новая игра', color=VkKeyboardColor.PRIMARY,
                                 payload=keyb_num * d.PAYLOAD_MULTIPLIER + 99)
    try:
        if not is_loose:
            gm_user.send_message(f'🌳 {game_str + 1}-й ход, текущая награда = {gm_user.count_rewards_mini_game2()}💰',
                                 keyb=keyboard.get_keyboard(),
                                 is_edit=True if game_str > 0 else False
                                 )
        else:
            gm_user.send_message(f'💀 {gm_user.src_name} проиграл, баланс {gm_user.balance - bet}💰',
                     keyboard.get_keyboard())
            return -1
    except vk_api.exceptions.ApiError:
        return d.MESSAGE_SEND_ERROR


def is_img_ready(gm_user):
    if gm_user.img != 'n' and gm_user.img_ready:
        return True


# def send_my_stalker(gm_user, result):  # для потока; экономит 2 секунды времени
#     if not gm_user.is_img_ready():
#         art = stalker.Stalker.character_image_generator(gm_user, cursor)
#         img = make_vk_image(art)
#         if not img:
#             blasthack(gm_user, '❌ Не удалось отправить изображение, попробуйте ещё раз')
#         else:
#             gm_user.img = img
#             gm_user.is_img_ready = True
#     else:
#         img = gm_user.img
#     inline_keyboard(gm_user, result, d.KEYBOARD_MY_STALKER, img)
#     sys.exit()
def critter_timeout(gm_user, current_time):
    if current_time - gm_user.hard_spam < d.MY_STALKER_TIMEOUT:
        return '❌ Эту команду можно выполнять не чаще, чем раз в ' + str(d.MY_STALKER_TIMEOUT) + ' секунд'
    gm_user.hard_spam = current_time


def send_critter_data():  #(gm_user, result, critter, keyboard=d.KEYBOARD_NONE):  # поточная
    while True:
        thrEvent.wait()
        while not d.MY_STALKER_QUEUE.empty():
            data = d.MY_STALKER_QUEUE.get()
            gm_user = data[0]
            result = data[1]
            critter = data[2]
            if len(data) > 3:
                keyboard = data[3]
            else:
                keyboard = d.KEYBOARD_NONE
            if not is_img_ready(critter):
                art = stalker.Stalker.character_image_generator(critter, cursor)
                img = make_vk_image(art)
                if not img:
                    blasthack(gm_user, '❌ Не удалось отправить изображение, попробуйте ещё раз')
                else:
                    critter.update_database_value(cursor, d.PLAYER_STALKER_IMAGE, img)
                    critter.img_ready = True
                    connect.commit()
            else:
                img = critter.img
            if keyboard == d.KEYBOARD_NONE:
                blasthack(gm_user, result, image=img)
            else:
                inline_keyboard(gm_user, result, keyboard, image=img)
            # sys.exit()
        thrEvent.clear()


threading.Thread(target=send_critter_data).start()


def send_auction_lots(gm_user, result):  # для потока; экономит 2 секунды времени
    number = 0
    for i in result:
        number += 1
        inline_keyboard(gm_user, i[1], [d.KEYBOARD_AUCTION_CHOOSE_LOT[0], str(number) + ') Купить 💰'], i[0])
    sys.exit()


def what_skills(gm_user, key_num):
    if not key_num:
        return
    if not str(key_num).isdigit():
        return
    key_num = int(key_num)
    if key_num // d.PAYLOAD_MULTIPLIER != d.KEYBOARD_FIGHT_MAGIC[0]:
        return
    gm_user.current_skill = key_num % d.PAYLOAD_MULTIPLIER


def admin_commands(admin, message):
    data = message.split(' ')
    if not (admin.user_id in d.ADMINISTRATORS):
        return
    try:
        if 'ban' in message:  # /ban id
            is_ban = 0 if 'unban' in message else 1
            _str = 'забанен' if is_ban else 'разбанен'
            target_id = int(data[1])
            if target_id in d.active_users:
                player = d.get_player(target_id)
                player.update_database_value(cursor, d.PLAYER_IS_BANED, is_ban)
                blasthack(player, f'Пользователь id{target_id} {_str}')
            cursor.execute(f'UPDATE users SET is_ban = {is_ban} WHERE user_id = {target_id}')
            blasthack(admin, f'Пользователь id{target_id} {_str}')
        # elif 'addstitem' in message:  # /addstitem target_id num count
        #     target_id = int(data[1])
        #     item_st_id = int(data[2])
        #     count = int(data[3])
        #     item_st = [item_st_id % d.BONUS_INTO_ID, d.STACKABLE_TYPE[item_st_id // d.BONUS_INTO_ID], count]
        #     if target_id in d.active_users:
        #         player = d.get_player(target_id)
        #         player.add_st_item(cursor=cursor, proto_type=item_st)
        #     else:
        #         cursor.execute(f'UPDATE items SET NS_item{item_st_id} = {count} WHERE user_id = {target_id}')
        #     blasthack(admin,
        #               f'Игрок id{target_id} получил {count} {stalker.get_stackable_item_name(cursor, [item_st_id])}')
        elif 'additem' in message:  # /additem target_id pid type
            target_id = int(data[1])
            item_pid = int(data[2])
            item_type = int(data[3])
            player = stalker.player_connect(target_id, cursor)
            player.add_item_to_database([item_pid, item_type], cursor)
            blasthack(admin, f'Игрок id{target_id} получил {stalker.get_item_name_proto(cursor, item_pid, item_type)}')
        elif 'changeparam' in message:  # /changeparam target_id name value
            target_id = int(data[1])
            param_name = data[2]
            param_value = int(data[3])
            player = stalker.player_connect(target_id, cursor)
            player.update_database_value(cursor, [0, param_name], param_value)
            blasthack(admin,
                      f'У пользователя id{target_id} был изменён параметр {param_name} на значение {param_value}')
        elif 'addtop' in message:
            target_id = int(data[1])
            mods = 0b1111 | stalker.get_bin_param(17)
            player = stalker.player_connect(target_id, cursor)
            player.add_item_to_database(proto_type=[101, d.TYPE_WEAPONS_ID], mods=mods, cursor=cursor)
            player.add_item_to_database(proto_type=[101, d.TYPE_WEAPONS_ID], mods=mods, cursor=cursor)
            player.add_item_to_database(proto_type=[101, d.TYPE_ARMOR_ID], mods=mods, cursor=cursor)
            blasthack(admin, f'Шмотки нарисованы id{target_id}')
        elif 'refresh':
            admin.update_database_value(cursor, d.PLAYER_RATING, 0)
            admin.update_database_value(cursor, d.PLAYER_ITEMS_RATING, 0)
            admin.add_bin_param(cursor, 31, d.BIN_TYPE_SKINS)
            blasthack(admin, f'Параметры администратора восстановлены')
    except IndexError:
        blasthack(admin, 'Неправильно заданы аргументы')
        return


# try:
def what_message(gm_user, message, key_num):
    # gm_user.add_bin_param(cursor, 4, d.BIN_TYPE_SKINS)
    if gm_user.is_ban == 1:
        return
    # if gm_user.user_id == 194322696:
    #    blasthack(gm_user, None, image='photo-213053803_457239417')
    #   return
    gm_user.peer_id = d.CURRENT_PEER_ID
    if d.CURRENT_PEER_ID:
        gm_user.update_database_value(cursor, d.PLAYER_LAST_PEER_ID, d.CURRENT_PEER_ID)

    if gm_user.user_id in d.ADMINISTRATORS and message[0] == '/':
        admin_commands(gm_user, message.lower())
        return

    if gm_user.is_busy:
        what_skills(gm_user, key_num)
        return
    current_time = time.time()
    protomes = message.lower()
    if current_time - gm_user.spam < 1:
        return
    gm_user.spam = current_time
    if key_num and str(key_num).isdigit():
        key_num = int(key_num)
        gm_user.keyboard = key_num // d.PAYLOAD_MULTIPLIER
    if not gm_user.keyboard:
        gm_user.keyboard = d.KEYBOARD_MAIN

    # ГЛАВНАЯ КЛАВИАТУРА
    if 'начать' in message.lower():
        blasthack(gm_user, '✋ Привет, я игровой бот. Для общения используй кнопки 🎹')
        return
    if gm_user.keyboard == d.KEYBOARD_MAIN:
        if '🗺 локации' in message.lower():
            inline_keyboard(gm_user, '🗺 Выбери локацию', d.KEYBOARD_LOCATIONS)
        elif '🎯 мини-игры' in message.lower():
            inline_keyboard(gm_user, '🎯 Выбирай, не задерживайся', d.KEYBOARD_MINI_GAME)
        elif '😎 мой сталкер' in message.lower():
            res = critter_timeout(gm_user, current_time)
            if res:
                blasthack(gm_user, res)
                return
            result = gm_user.get_player_data()
            d.MY_STALKER_QUEUE.put([gm_user, result, gm_user, d.KEYBOARD_MY_STALKER])
            thrEvent.set()
            # threading.Thread(target=send_critter_data,
            #                  args=(gm_user, result, gm_user, d.KEYBOARD_MY_STALKER)).start()  # затратна по времени, требуется отдельный поток
        elif '💀 охота' in message.lower():
            if gm_user.bar == 0:
                cr = d.MINI_BOSS_OBJECT
                inline_keyboard(gm_user, f'💀 Здесь появляются сталкеры, '
                                         f'за головы которых назначена награда.\n 🔪Текущий сталкер: '
                                         f'{cr.user_name}\n♻ Основные характеристики:\n'
                                         f'❣ Здоровье: {cr.max_hp}\n'
                                         f'🔪 Урон: {cr.damage}\n'
                                         f'🛡 Защита: {cr.armor}\n'
                                         f'🎲 Крит: {cr.crit_chance}\n'
                                         f'🎁 Награда: {cr.reward[0][0]}💰\n',
                                d.KEYBOARD_HUNTING, image=cr.source)
            else:
                blasthack(gm_user, '⚔ Ты уже охотился на текущего сталкера, подожди следующего')
                return
        elif '⚖ аукцион' in message.lower():
            inline_keyboard(gm_user, '⚖ Здесь можно торговать с другими сталкерами', d.KEYBOARD_AUCTION)
        elif '💼 инвентарь' in message.lower():
            temp = gm_user.generate_item_list_for_inventory()
            text = temp + '\n🔎 Выбирай, что рассмотреть поближе'
            inline_keyboard(gm_user, text, d.KEYBOARD_INVENTORY, is_callback=True)
        elif '🔥 акции' in message.lower():
            inline_keyboard(gm_user, '🔥 Воспользуйся, если нехватает на волыну', d.KEYBOARD_SALES)
        elif '🐲 боссы' in message.lower():
            for group in d.wait_group_follow:
                if group[1] == gm_user:
                    inline_keyboard(gm_user,
                                    f'❓ Игрок {group[0].src_name} пригласил тебя в группу',
                                    d.KEYBOARD_GROUP_WAIT_FOLLOW_ANSWER)
            if gm_user.group_id in d.wait_boss_fight.keys():
                boss = stalker.Boss(d.wait_boss_fight[gm_user.group_id][0], cursor)
                inline_keyboard_specifik(gm_user,
                                         f'Твоя команда хочет сразиться с боссом {boss.user_name}, участвуешь?',
                                         d.KEYBOARD_GROUP_WAIT_BOSS_FIGHT, d.MESSAGE_FLAG_NO_LINE)
            data = gm_user.get_location_bosses(cursor)
            if data == d.ERROR:
                blasthack(gm_user, '❌ На этой локации нет боссов')
            numbers_keyboard(gm_user, data[0], 1, data[1], key_num=d.KEYBOARD_BOSS_SELECT[0])
            gm_user.keyboard = d.KEYBOARD_BOSS_SELECT[0]
        elif '⚔ арена' in message.lower():
            for arena in d.wait_arena_follow:
                if arena[1] == gm_user:
                    inline_keyboard(gm_user,
                                    f'❓ Игрок {arena[0].src_name} пригласил тебя на арену',
                                    d.KEYBOARD_ARENA_WAIT_FOLLOW_ANSWER)
            inline_keyboard(gm_user, '⚔ Здесь можно заработать денег и славу', d.KEYBOARD_ARENA,
                            image=d.ARENA_PICTURE)
        elif '🎁 хабар' in message.lower():
            inline_keyboard(gm_user, '🎁 В этих кейсах может быть что угодно от консервных банок до экзоскелета',
                            d.KEYBOARD_LOOT)
        elif '📁 прочее' in message.lower():
            inline_keyboard(gm_user, '📁 Здесь расположен бонусный контент по игре', d.KEYBOARD_OTHER)
        elif '🌎 ссылки' in message.lower():
            # inline_keyboard(gm_user, '&#128240; Чаты и беседы Сталкеров', d.KEYBOARD_SOURCE)
            inline_keyboard(gm_user, '🌎 Ссылки появятся после релиза', d.KEYBOARD_SOURCE)
        elif '💰 магазин' in message.lower():
            # inline_keyboard(gm_user, '&#128755; Админу на консервы', d.KEYBOARD_DONUT)
            inline_keyboard(gm_user, '💰 Здесь можно покупать различные предметы', d.KEYBOARD_DONUT)
        else:
            fail_message(gm_user)
        return
    # Inline клавиатуры, проверяется только одна в зависимости от параметра

    # Локации-----------------------------------------------------------------------------------
    elif gm_user.keyboard == d.KEYBOARD_LOCATIONS[0]:
        for i in range(1, len(d.KEYBOARD_LOCATIONS)):
            if protomes in d.KEYBOARD_LOCATIONS[i].lower():
                blasthack(gm_user, f'Локация изменена на {d.KEYBOARD_LOCATIONS[i]}')
                gm_user.location = i
                gm_user.update_database_value(cursor, d.PLAYER_LOCATION, gm_user.location)
                break
            if i == (len(d.KEYBOARD_LOCATIONS) - 1):
                blasthack(gm_user, d.DEFAULT_BOT_ANSWER)
        gm_user.keyboard = d.KEYBOARD_MAIN
        return
    # -----------------------------------------------------------------------------------

    # Мини игры-----------------------------------------------------------------------------------
    elif gm_user.keyboard == d.KEYBOARD_MINI_GAME[0]:
        if protomes in d.KEYBOARD_MINI_GAME[1].lower():
            inline_keyboard(gm_user,
                            '🕹 В этой игре я подбрасываю монетку. Если выпадет орёл - ты выйграл и ставка '
                            'удваивается, если решка - ты проиграл', d.KEYBOARD_MINI_GAME1, image=d.MONETKA_PICTURE)
            gm_user.keyboard = d.KEYBOARD_MINI_GAME1[0]
        elif protomes in d.KEYBOARD_MINI_GAME[2].lower():
            inline_keyboard_specifik(gm_user,
                                     '🌲 В этой игре тебе предстоит исследовать тайны зоны. Выбери размер исследуемой области. Чем'
                                     ' меньше область, тем выше плотность аномалий и больше награда',
                                     d.KEYBOARD_MINI_GAME2, d.MESSAGE_FLAG_NO_LINE)
            gm_user.end_mini_game()
        elif protomes in d.KEYBOARD_MINI_GAME[3].lower():
            inline_keyboard(gm_user, '🎲 В этой игре я прячу шарик за одним из напёрстков. Угадай где он, '
                                     'чтобы победить', d.KEYBOARD_MINI_GAME3, image=d.NAPERSTKI_PICTURE)
            gm_user.keyboard = d.KEYBOARD_MINI_GAME3[0]
        else:
            fail_message(gm_user)
        return

    # Мини игра Напёрстки
    elif gm_user.keyboard == d.KEYBOARD_MINI_GAME3[0]:
        if not key_num:
            return
        if key_num % d.PAYLOAD_MULTIPLIER == 0:
            inline_keyboard_specifik(gm_user,
                                     f'🎰 Введи сумму ставки, У тебя на балансе {gm_user.balance}💰',
                                     d.KEYBOARD_MINI_GAME3_1, d.MESSAGE_FLAG_NO_LINE)
        else:
            fail_message(gm_user)
        return

    # Выбор ставки для игры монетка
    elif gm_user.keyboard == d.KEYBOARD_MINI_GAME3_1[0]:
        err = check_bet(gm_user, message)
        if err:
            blasthack(gm_user, err)
            return
        price = int(message)
        gm_user.temp_data = [d.TEMP_MINI_GAME3_INDEX, price]
        gm_user.send_message('🔍 Выбирай напёрсток', template=d.CAROUSEL_KEYBOARD, keyb=None)
        gm_user.keyboard = d.KEYBOARD_MINI_GAME3_2[0]
        return

    elif gm_user.keyboard == d.KEYBOARD_MINI_GAME3_2[0]:
        if not key_num or not gm_user.temp_data:
            return
        if gm_user.temp_data[0] != d.TEMP_MINI_GAME3_INDEX:
            return
        choose = key_num % d.PAYLOAD_MULTIPLIER
        if choose > 2 or choose < 0:
            return
        if d.GAME_RANDOM.Random(0, 2) == choose:
            price = gm_user.temp_data[1] * 2
            mes = '➕ Ты выйграл'
            att = 'photo-210036099_457240288'
        else:
            price = -gm_user.temp_data[1]
            mes = '➖ Ты проиграл'
            att = 'photo-210036099_457240289'
        gm_user.update_user_balance(cursor, price)
        mes += f'! Баланс {gm_user.balance}💰'
        inline_keyboard(gm_user, mes, [d.KEYBOARD_MINI_GAME3[0], '🔥 Сыграть ещё'], image=att)
        gm_user.temp_data = []
        return

    # Мини игра Монетка
    elif gm_user.keyboard == d.KEYBOARD_MINI_GAME1[0]:
        if protomes in d.KEYBOARD_MINI_GAME1[1].lower():
            inline_keyboard_specifik(gm_user,
                                     f'🎰 Введи сумму ставки, У тебя на балансе {gm_user.balance}💰',
                                     d.KEYBOARD_MINI_GAME1_1, d.MESSAGE_FLAG_NO_LINE)
        else:
            fail_message(gm_user)
        return

    # Выбор ставки для игры монетка
    elif gm_user.keyboard == d.KEYBOARD_MINI_GAME1_1[0]:
        err = check_bet(gm_user, message)
        if err:
            blasthack(gm_user, err)
            return
        price = int(message)
        result = d.GAME_RANDOM.Random(0, 1)
        if result == 1:
            gm_user.balance += price
        else:
            gm_user.balance -= price
        gm_user.update_database_value(cursor, d.PLAYER_BALANCE, gm_user.balance)
        gm_user.last_stavka = price
        inline_keyboard(gm_user, ('Ты выйграл!' if result == 1 else '➖ Ты проиграл!') + ' Баланс = ' + str(
            gm_user.balance) + '💰', d.KEYBOARD_MINI_GAME1_2)
        gm_user.keyboard = d.KEYBOARD_MINI_GAME1_2[0]
        return

    # повтор ставки для игры монетка
    elif gm_user.keyboard == d.KEYBOARD_MINI_GAME1_2[0]:
        if protomes in d.KEYBOARD_MINI_GAME1_2[1].lower():
            price = gm_user.last_stavka
            err = check_bet(gm_user, str(price))
            if err:
                blasthack(gm_user, err)
                return
            result = d.GAME_RANDOM.Random(0, 1)
            if result == 1:
                gm_user.balance += price
            else:
                gm_user.balance -= price
            gm_user.update_database_value(cursor, d.PLAYER_BALANCE, gm_user.balance)
            inline_keyboard(gm_user, ('Ты выйграл!' if result == 1 else '➖ Ты проиграл!') + ' Баланс = ' + str(
                gm_user.balance) + '💰', d.KEYBOARD_MINI_GAME1_2)
            gm_user.keyboard = d.KEYBOARD_MINI_GAME1_2[0]
        elif protomes in d.KEYBOARD_MINI_GAME1_2[2].lower():
            inline_keyboard_specifik(gm_user,
                                     '🎰 Введи сумму ставки, У тебя на балансе ' + str(gm_user.balance) +
                                     '💰', d.KEYBOARD_MINI_GAME1_1, d.MESSAGE_FLAG_NO_LINE)
            gm_user.keyboard = d.KEYBOARD_MINI_GAME1_1[0]
        else:
            fail_message(gm_user)
        return

    # Исследователь
    elif gm_user.keyboard == d.KEYBOARD_MINI_GAME2[0]:
        if protomes in d.KEYBOARD_MINI_GAME2[1:]:
            if gm_user.temp_data:
                if gm_user.temp_data[0] == d.TEMP_MINI_GAME2_INDEX:
                    return
            gm_user.temp_data = [d.TEMP_MINI_GAME2_INDEX, int(protomes)]
            inline_keyboard_specifik(gm_user,
                                     '🎰 Введи сумму ставки, У тебя на балансе ' + str(gm_user.balance) +
                                     '💰', d.KEYBOARD_MINI_GAME2_1, d.MESSAGE_FLAG_NO_LINE)
        return

    # создание игровой клавиатуры
    elif gm_user.keyboard == d.KEYBOARD_MINI_GAME2_1[0]:
        if not gm_user.temp_data or gm_user.temp_data[0] != d.TEMP_MINI_GAME2_INDEX or len(gm_user.temp_data) > 2:
            return
        err = check_bet(gm_user, message)
        if err:
            blasthack(gm_user, err)
            return
        value = int(message)
        gm_user.last_stavka = value
        gm_user.temp_data.append(value)  # третий аргумент, размер ставки ([2])
        gm_user.temp_data.append(0)  # четвертый аргумент, номер поля ([3])
        gm_user.temp_data.append({})  # пятый аргумент, поля со взрывами ([4])
        mini_game2_keyboard(gm_user)
        return

    # игровой процесс
    elif gm_user.keyboard == d.KEYBOARD_MINI_GAME2_2[0]:
        if not key_num:
            return
        click = (key_num % d.PAYLOAD_MULTIPLIER)
        if gm_user.temp_data and gm_user.temp_data[0] == d.TEMP_MINI_GAME2_INDEX and len(gm_user.temp_data) >= 5:
            tmp_val = gm_user.temp_data
            rows = tmp_val[1]  # количество линий
            bet = tmp_val[2]  # ставка
            game_str = tmp_val[3]  # номер хода, начинается с 0
            if click % 5 == game_str and click < 97:
                gm_user.temp_data[4][game_str] = [d.GAME_RANDOM.Random(0, rows - 1), click // 5]
                gm_user.temp_data[3] += 1
                data = mini_game2_keyboard(gm_user)
                if data == -1:
                    gm_user.update_user_balance(cursor, -bet)
                    gm_user.end_mini_game()
                    return
                elif data == d.MESSAGE_SEND_ERROR:
                    gm_user.temp_data[3] -= 1
                    return
                elif gm_user.temp_data[3] == 5:
                    click = 97
            if click == 97:
                gm_user.update_user_balance(cursor, + gm_user.count_rewards_mini_game2() - bet)
                blasthack(gm_user, f'🎉 {gm_user.src_name} победил, баланс {gm_user.balance}💰')
                gm_user.end_mini_game()
                return
        if click == 98:
            blasthack(gm_user, '❌ Игра отменена')
            gm_user.end_mini_game()
        elif click == 99:
            gm_user.end_mini_game()
            inline_keyboard_specifik(gm_user, '🌲 Игра перезапущена. Выбери размер области', d.KEYBOARD_MINI_GAME2,
                                     d.MESSAGE_FLAG_NO_LINE)
        elif not gm_user.temp_data or gm_user.temp_data[0] != d.TEMP_MINI_GAME2_INDEX or len(gm_user.temp_data) < 5:
            blasthack(gm_user, d.DEFAULT_BOT_ANSWER)

    # -----------------------------------------------------------------------------------------------------------------

    # Мой сталкер -----------------------------------------------------------------------------------------------------
    elif gm_user.keyboard == d.KEYBOARD_MY_STALKER[0]:  # фоны
        if not key_num:
            fail_message(gm_user)
            return
        if protomes in d.KEYBOARD_MY_STALKER[1].lower() or key_num % d.PAYLOAD_MULTIPLIER == 0:
            data = gm_user.get_player_skins(cursor, bg=True)
            gm_user.send_message(data[0], data[1])
        elif protomes in d.KEYBOARD_MY_STALKER[2].lower() or key_num % d.PAYLOAD_MULTIPLIER == 1:  # cкины
            data = gm_user.get_player_skins(cursor)
            gm_user.send_message(data[0], data[1])
            return
        elif protomes in d.KEYBOARD_MY_STALKER[3].lower():
            blasthack(gm_user, '✏ Введите ник (до 15 символов)')  # изменить ник
            gm_user.keyboard = d.KEYBOARD_CHANGE_NICKNAME[0]
        elif protomes in d.KEYBOARD_MY_STALKER[4].lower():  # снять шмот
            # gm_user.move_items_from_skin(cursor, connect)
            # blasthack(gm_user, '✅ Предметы были перенесены в инвентарь')
            inline_keyboard(gm_user, '👖 Выбирай', d.KEYBOARD_REMOVE_CLOTHES)
        elif protomes in d.KEYBOARD_MY_STALKER[5].lower():  # навыки
            result = gm_user.show_player_skills()
            if not result:
                return
            blasthack(gm_user, result)
        elif protomes in d.KEYBOARD_MY_STALKER[
            6].lower():  # рейтинг (отличается от аренного если шо), генерится по статам шмота
            data = gm_user.get_item_rating(cursor)
            inline_keyboard(gm_user, data, d.KEYBOARD_SHOW_RATING_CRIT, is_callback=True)
        elif protomes in d.KEYBOARD_MY_STALKER[7].lower():  # помощь
            blasthack(gm_user,
                      '📄 Информацию об игре смотрите по ссылке https://vk.com/@-210036099-stalker-bot-beta-instrukciya')
        elif protomes in d.KEYBOARD_MY_STALKER[8].lower():  # все параметры
            blasthack(gm_user, gm_user.show_all_player_params())
        else:
            fail_message(gm_user)
        return

    # Изменить никнейм
    elif gm_user.keyboard == d.KEYBOARD_CHANGE_NICKNAME[0]:
        if len(message) == 0 or len(message) > 30:
            return
        message = "".join([z for _d in ' '.join(a for a in message.split()) for x in _d for z in x if
                           z.isalnum() or z == ' ']).replace("  ", " ")
        if len(message) == 0 or message == ' ' or message.isdigit():
            blasthack(gm_user, '❌ Ник не подходит')
            return
        text = message[0:min(15, len(message))]
        if 'admin' in text.lower() and gm_user.user_id not in d.ADMINISTRATORS:  # лень делать полноценную проверку на уникальность
            blasthack(gm_user, '❌ Этот ник занят')
            return
        # if 'http' in text.lower() or '/' in text.lower() or '.' in text.lower():
        #     blasthack(gm_user, '❌ Ссылки в никах запрещены')
        #     return
        gm_user.user_name = text
        gm_user.update_database_value(cursor, d.PLAYER_USERNAME, text)
        gm_user.src_name = f'[id{gm_user.user_id}|{gm_user.user_name}]'
        blasthack(gm_user, '✅ Ник был изменён на ' + gm_user.user_name)
        gm_user.keyboard = d.KEYBOARD_MY_STALKER[0]
        return

    # Раздеть сталкера

    elif gm_user.keyboard == d.KEYBOARD_REMOVE_CLOTHES[0]:
        if d.KEYBOARD_REMOVE_CLOTHES[1] in message:
            if gm_user.move_item_from_skin(cursor, connect, d.PLAYER_LEFT_HAND) or gm_user.move_item_from_skin(cursor, connect, d.PLAYER_RIGHT_HAND):
                blasthack(gm_user, '✅ Оружие перенесено в инвентарь')
        elif d.KEYBOARD_REMOVE_CLOTHES[2] in message:
            if gm_user.move_item_from_skin(cursor, connect, d.PLAYER_ARMOR_ITEM):
                blasthack(gm_user, '✅ Броня перенесена в инвентарь')
        elif d.KEYBOARD_REMOVE_CLOTHES[3] in message:
            if gm_user.move_item_from_skin(cursor, connect, d.PLAYER_HELMET):
                blasthack(gm_user, '✅ Шлем перенесен в инвентарь')
        elif d.KEYBOARD_REMOVE_CLOTHES[4] in message:
            if gm_user.move_item_from_skin(cursor, connect, d.PLAYER_ARTEFACT):
                blasthack(gm_user, '✅ Артефакт перенесен в инвентарь')
        elif d.KEYBOARD_REMOVE_CLOTHES[5] in message:
            gm_user.move_items_from_skin(cursor, connect)
            blasthack(gm_user, '✅ Предметы были перенесены в инвентарь')
        else:
            fail_message(gm_user)
        return

    elif gm_user.keyboard == d.KEYBOARD_SHOW_RATING_CRIT[0]:
        num = get_button_number(key_num)
        if not gm_user.rating_lst:
            return
        if -1 < num < 8:
            if len(gm_user.rating_lst) < num+2:
                return
            target = stalker.player_connect(gm_user.rating_lst[num+1], cursor)
            d.MY_STALKER_QUEUE.put([gm_user, None, target])
            thrEvent.set()

            # threading.Thread(target=send_critter_data,
            #                  args=(
            #                      gm_user, None, target)).start()
        elif num == 8:
            inline_keyboard(gm_user, gm_user.get_arena_rating(cursor, gm_user.rating_lst[0], is_top=True), d.KEYBOARD_SHOW_RATING_CRIT, is_edit=True, is_callback=True)
        elif num == 9:
            inline_keyboard(gm_user, gm_user.get_arena_rating(cursor, gm_user.rating_lst[0]), d.KEYBOARD_SHOW_RATING_CRIT, is_edit=True, is_callback=True)
        else:
            fail_message(gm_user)
        return
    # ----------------------------------------------------------------------------------------------------------------

    # Охота --------------------------------------------------------------------------------------------------------
    elif gm_user.keyboard == d.KEYBOARD_HUNTING[0]:
        if gm_user.bar:
            blasthack(gm_user, '⚔ Ты уже охотился на текущего сталкера, подожди следующего')
            return
        if protomes in d.KEYBOARD_HUNTING[1].lower():
            if gm_user.energy < d.BOSS_FIGHT_PRICE:
                blasthack(gm_user, '❌ Недостаточно энергии для боя с боссом')
                return
            blasthack(gm_user, '🔥 Бой скоро начнётся')
            combat = stalker.Combat([gm_user], [deepcopy(d.MINI_BOSS_OBJECT)], d.COMBAT_TYPE_BOSS)
            combat.add_combat_to_combats()
            gm_user.update_database_value(cursor, d.PLAYER_BAR_ID, 1)
        else:
            fail_message(gm_user)
        return
    # ----------------------------------------------------------------------------------------------------------------

    # Аукцион --------------------------------------------------------------------------------------------------------
    elif gm_user.keyboard == d.KEYBOARD_AUCTION[0]:
        if protomes in d.KEYBOARD_AUCTION[1].lower():
            result = gm_user.get_user_lots(cursor)
            if result[0]:
                inline_keyboard(gm_user, result[0], result[1])
            else:
                blasthack(gm_user, '❌ У вас нет лотов')
        elif protomes in d.KEYBOARD_AUCTION[2].lower():
            result = gm_user.look_auction_lots(cursor)
            if not result:
                blasthack(gm_user, '❌ Нет товаров, соответствующих вашему балансу')
                return
            threading.Thread(target=send_auction_lots, args=(gm_user, result)).start()  # затратно по времени
        elif protomes in d.KEYBOARD_AUCTION[3].lower():
            blasthack(gm_user, '✏ Введите название предмета')
            gm_user.keyboard = d.KEYBOARD_AUCTION_WAIT_NAME[0]
        elif protomes in d.KEYBOARD_AUCTION[4].lower():
            blasthack(gm_user, '✏ Введите сумму и id пользователя через пробел. Пример: 500 12345678')
            gm_user.keyboard = d.KEYBOARD_AUCTION_WAIT_SUM[0]
        elif protomes in d.KEYBOARD_AUCTION[5].lower():
            gm_user.return_all_user_items(cursor)
            blasthack(gm_user, '✅ Предметы были перемещены в инвентарь')
        else:
            fail_message(gm_user)
        return

    # выставление предмета на аукцион из инвентаря
    elif gm_user.keyboard == d.KEYBOARD_AUCTION_CONTINUE[0]:
        price = check_valid_sum(gm_user, message)
        if price == d.ERROR:
            return
        gm_user.move_item_to_auction(cursor, price)
        gm_user.selected_item = None
        blasthack(gm_user, '✅ Предмет выставлен на аукцион')

    # подробное отображение одного из своих лотов
    elif gm_user.keyboard == d.KEYBOARD_AUCTION_SELECT_LOT[0]:
        if d.KEYBOARD_INVENTORY_ANSWERS[0] in message:
            if gm_user.auction_page == 0:
                return
            gm_user.auction_page -= 1
            result = gm_user.get_user_lots(cursor)
            inline_keyboard(gm_user, result[0], result[1])
            return
        elif d.KEYBOARD_INVENTORY_ANSWERS[9] in message:
            gm_user.auction_page += 1
            result = gm_user.get_user_lots(cursor)
            inline_keyboard(gm_user, result[0], result[1])
            return
        if not d.EMOJI_NUMBER_ASSOTIATIONS.get(message):
            number = check_valid_sum(gm_user, message, False)
        else:
            number = d.EMOJI_NUMBER_ASSOTIATIONS[message]
        if not gm_user.temp_data:
            return
        if len(gm_user.temp_data) < (number + 1) or gm_user.temp_data[
            0] != d.LOTS_ID_FROM_AUCTION or number == d.ERROR:
            blasthack(gm_user, '❌ Введён некорректный номер')
            return
        # number += gm_user.auction_page * d.ITEMS_IN_ONE_PAGE
        uid = gm_user.temp_data[number]
        result = gm_user.draw_selected_auction_lot(cursor, uid)
        inline_keyboard(gm_user, result[1], d.KEYBOARD_AUCTION_SELECT_LOT_2, result[0])

    # удаление лота с аукциона и перемещение в инвентарь
    elif gm_user.keyboard == d.KEYBOARD_AUCTION_SELECT_LOT_2[0]:
        if protomes in d.KEYBOARD_AUCTION_SELECT_LOT_2[1].lower():
            if not gm_user.temp_data:
                return
            if not (gm_user.temp_data[0] == d.SELECTED_LOT_FROM_AUCTION and len(gm_user.temp_data) == 2):
                gm_user.temp_data = []
                blasthack(gm_user, '❌ Некорректные данные')
                return
            gm_user.move_item_from_auction(cursor)
            blasthack(gm_user, '✅ Лот был перемещён в инвентарь')
            gm_user.keyboard = d.KEYBOARD_AUCTION_SELECT_LOT[0]
        else:
            fail_message(gm_user)
        return

    # покупка товара
    elif gm_user.keyboard == d.KEYBOARD_AUCTION_CHOOSE_LOT[0]:
        number = check_valid_sum(gm_user, message[0], False)
        if not gm_user.temp_data:
            return
        if len(gm_user.temp_data) < (number + 1) or gm_user.temp_data[
            0] != d.SOME_ITEMS_FROM_AUCTION or number == d.ERROR:
            blasthack(gm_user, '❌ Введён некорректный номер')
            gm_user.keyboard = d.KEYBOARD_MAIN
            return
        uid = gm_user.temp_data[number]
        err = gm_user.buy_item_from_auction(uid, cursor)
        if err == d.ERROR:
            blasthack(gm_user, '❌ Недостаточно денег для покупки')
            return
        elif err == d.ITEM_NOT_FOUND_ERROR:
            blasthack(gm_user, '❌ Лот не найден')
            return
        else:
            blasthack(gm_user, '✅ Лот успешно приобретён')
            blasthack(err, f'⚖ Один из ваших лотов был куплен, баланс {err.balance}💰')

    # вывод товаров по названию
    elif gm_user.keyboard == d.KEYBOARD_AUCTION_WAIT_NAME[0]:
        result = gm_user.get_lots_from_name(message, cursor)
        if not result:
            blasthack(gm_user, '❌ Нет товаров с таким названием')
            return
        threading.Thread(target=send_auction_lots, args=(gm_user, result)).start()  # затратно по времени

    # перевод денег пользователю
    elif gm_user.keyboard == d.KEYBOARD_AUCTION_WAIT_SUM[0]:
        data = message.split(' ')
        if len(data) == 1:
            return
        money = check_valid_sum(gm_user, data[0], False)
        recipient = check_valid_sum(gm_user, data[1], False)
        if money == d.ERROR or recipient == d.ERROR:
            blasthack(gm_user, '❌ Некорректные данные')
            return
        err = gm_user.transfer_money(recipient, money, cursor)
        if err == d.NEED_MORE_MONEY_ERROR:
            blasthack(gm_user, '❌ Недостаточно денег')
            return
        elif err == d.PLAYER_NOT_FOUND_ERROR:
            blasthack(gm_user, '❌ Игрок не найден')
            return
        blasthack(gm_user, '✅ Успешно, баланс: ' + str(gm_user.balance))
        blasthack(err, f'Игрок {gm_user.src_name} перевёл тебе {money}💰')
        return

    # ----------------------------------------------------------------------------------------------------------------

    # Работа с инвентарём---------------------------------------------------------------------------------------------
    elif gm_user.keyboard == d.KEYBOARD_INVENTORY[0]:
        num = get_button_number(key_num)
        if num == -1:
            tmp_val = 1
            for item in gm_user.items_obj:
                it_name = item.name.replace("_", " ")
                if message.lower() in it_name.lower():
                    gm_user.inventory_page = tmp_val // 8
                    num = tmp_val % 8
                    break
                tmp_val += 1
        if num == 0 or num == 9:
            if num == 0:
                if gm_user.inventory_page == 0:
                    return
                gm_user.inventory_page -= 1
            elif num == 9:
                gm_user.inventory_page += 1
                if gm_user.inventory_page * 8 >= len(gm_user.items_obj):
                    gm_user.inventory_page -= 1
                    return
            temp = gm_user.generate_item_list_for_inventory()
            text = temp + '\n🔎 Выбирай, что рассмотреть поближе'
            inline_keyboard(gm_user, text, d.KEYBOARD_INVENTORY, is_edit=True, is_callback=True)
        elif 0 < num < 9:
            data = gm_user.look_all_items_param(num, cursor)
            if data == d.ITEM_NOT_FOUND_ERROR:
                return
            inline_keyboard(gm_user, data[1], data[2], data[0])
            gm_user.keyboard = d.KEYBOARD_SET_SELECTED_ITEM[0]

        else:
            fail_message(gm_user)
        return

    # Взаимодействие с выбранным в инвентаре предметом
    elif gm_user.keyboard == d.KEYBOARD_SET_SELECTED_ITEM[0]:
        if not gm_user.selected_item:
            blasthack(gm_user, '❌ Выбранный предмет пропал из инвентаря')
            return
        if d.KEYBOARD_SET_SELECTED_ITEM[1] in message:
            err = gm_user.move_item_to_skin(cursor, connect)
            if err == d.NO_STACK_ERROR:
                blasthack(gm_user, '❌ Предмет не может быть надет')
            elif err == d.SLOT_IS_BUSY_ERROR:
                blasthack(gm_user, '❌ Все слоты для этого предмета заняты')
            elif err == d.SUCCESSFUL:
                gm_user.keyboard = d.KEYBOARD_MAIN
                blasthack(gm_user, '✅ Предмет успешно надет')
                gm_user.selected_item = None
            gm_user.keyboard = d.KEYBOARD_INVENTORY[0]
        elif d.KEYBOARD_SET_SELECTED_ITEM[2] in message:
            data = gm_user.get_valid_mode_list(cursor)
            if data == d.NO_STACK_ERROR:
                blasthack(gm_user, '❌ Предмет не может иметь модификаций')
                return
            elif data == d.NO_HAVE_MODS_ERROR:
                blasthack(gm_user, '❌ У вас нет модов на данный предмет')
                return
            inline_keyboard(gm_user, data[0], data[1])
            gm_user.keyboard = d.KEYBOARD_ADD_MODE_TO_ITEM[0]
        elif d.KEYBOARD_SET_SELECTED_ITEM[3] in message:
            if not gm_user.selected_item.is_stackable():
                inline_keyboard(gm_user, '♻ Вы уверены?', d.KEYBOARD_VERIFICATION)
                return
            data = gm_user.sell_item_default(cursor)
            if data == d.NEED_MORE_DATA_ERROR:
                inline_keyboard_specifik(gm_user, '❓ Сколько?', d.KEYBOARD_COUNT_OF_SELL_ITEMS,
                                         d.MESSAGE_FLAG_NO_LINE)
                return
            blasthack(gm_user, f'✅ Предмет продан. Баланс: {data} &#128176;')
            gm_user.selected_item = None
            gm_user.keyboard = d.KEYBOARD_MAIN
        elif d.KEYBOARD_SET_SELECTED_ITEM[4] in message:
            # item_type = gm_user.selected_item.type
            # if item_type in d.STACKABLE_TYPE:
            #     blasthack(gm_user, '❌ Этот предмет нельзя выставить на аукцион')
            #     return
            blasthack(gm_user, '❓ Укажите цену на предмет')
            gm_user.keyboard = d.KEYBOARD_AUCTION_CONTINUE[0]
        elif d.KEYBOARD_SET_SELECTED_ITEM[5] in message:
            item = gm_user.selected_item
            res = gm_user.loot_case_open(cursor, item)
            if res != d.ERROR:
                blasthack(gm_user, res)
                gm_user.keyboard = d.KEYBOARD_MAIN
            else:
                blasthack(gm_user, '❌ У вас нет кейсов данного типа')
        elif d.KEYBOARD_SET_SELECTED_ITEM[6] in message:
            item = gm_user.selected_item
            if item.iznos >= 100:
                blasthack(gm_user, '❌ Предмет не нуждается в ремонте')
                return
            item.iznos = min(item.iznos, 100)
            rem_price = int((100 - item.iznos) * item.price * 0.001)
            inline_keyboard(gm_user, f"🛠 Цена ремонта {rem_price}💰.", d.KEYBOARD_REMONT)
        elif d.KEYBOARD_SET_SELECTED_ITEM[7] in message:
            item = gm_user.selected_item
            gm_user.use_item(item, cursor)
        else:
            fail_message(gm_user)
        return

    elif gm_user.keyboard == d.KEYBOARD_REMONT[0]:
        if not gm_user.selected_item:
            blasthack(gm_user, '❌ Выбранный предмет пропал из инвентаря')
            return
        if d.KEYBOARD_REMONT[1] in message:
            item = gm_user.selected_item
            _price = int((100 - item.iznos) * item.price * 0.001)
            if gm_user.balance < _price:
                blasthack(gm_user, "❌ Недостаточно денег для ремонта")
                return
            gm_user.update_user_balance(cursor, -_price)
            item.iznos = 100
            item.update_param("iznos", 100, cursor)
            blasthack(gm_user, "✅ Предмет отремонтирован")
        elif d.KEYBOARD_REMONT[2] in message:
            pass
        else:
            fail_message(gm_user)
        return

    # Подтверждение продажи предмета
    elif gm_user.keyboard == d.KEYBOARD_VERIFICATION[0]:
        if not gm_user.selected_item:
            blasthack(gm_user, '❌ Выбранный предмет пропал из инвентаря')
            return
        if d.KEYBOARD_VERIFICATION[1] in message:
            data = gm_user.sell_item_default(cursor)
            blasthack(gm_user, f'✅ Предмет продан. Баланс: {data} &#128176;')
            gm_user.selected_item = None
            gm_user.keyboard = d.KEYBOARD_MAIN
        elif d.KEYBOARD_VERIFICATION[2] in message:
            blasthack(gm_user, '❌ Продажа отменена')
        else:
            fail_message(gm_user)
        return
    #//////////////////////////////////////////////////////////////////////

    # Добавление мода на предмет
    elif gm_user.keyboard == d.KEYBOARD_ADD_MODE_TO_ITEM[0]:
        if not gm_user.selected_item:
            blasthack(gm_user, '❌ Предмет исчез из инвентаря')
            return
        start = message.find('(')
        if start == -1:
            return
        end = message.find(')')
        if end == -1:
            return
        st_item_id = int(message[start + 1:end])
        res = gm_user.add_mod_to_item(st_item_id, False, cursor)
        if res == d.ITEM_NOT_FOUND_ERROR:
            blasthack(gm_user, '❌ У вас нет модов данного типа в инвентаре')
        elif res == d.SLOT_IS_BUSY_ERROR:
            blasthack(gm_user, '❌ Такой мод уже установлен на предмет')
        else:
            blasthack(gm_user, '✅ Мод успешно установлен')
        return

    # быстрая продажа предметов
    elif gm_user.keyboard == d.KEYBOARD_COUNT_OF_SELL_ITEMS[0]:
        if not gm_user.selected_item:
            blasthack(gm_user, '❌ Предмет исчез из инвентаря')
            return
        count = check_valid_sum(gm_user, message)
        if count == d.ERROR:
            return
        data = gm_user.sell_item_default_continue(cursor, count)
        if data == d.NOT_ENOUGH_ITEMS_ERROR:
            blasthack(gm_user, '❌ У вас недостаточно предметов')
            return
        blasthack(gm_user, '➕ Предмет продан. Баланс: ' + str(data) + '💰')
        gm_user.keyboard = d.KEYBOARD_MAIN

    # ----------------------------------------------------------------------------------------------------------------

    # Акции (в основном сидорович)------------------------------------------------------------------------------------
    elif gm_user.keyboard == d.KEYBOARD_SALES[0]:
        if protomes in d.KEYBOARD_SALES[1].lower():
            if gm_user.ref_src == 'n':
                ref_string = f"https://vk.me/public{d.GROUP_BOT_ID}?ref={gm_user.user_id}"
                d.MESSAGES_QUEUE.put(['utils.getShortLink', {'url': ref_string}, gm_user.user_id])
                # ref_string = d.BH.method('utils.getShortLink', {'url': ref_string})
                # ref_string = ref_string['short_url']
                # gm_user.update_database_value(cursor, d.PLAYER_REF_SRC, ref_string)
            else:
                ref_string = gm_user.ref_src
                blasthack(gm_user,
                          f'🗺 На кордоне есть торговец по имени Сидорович 👴. Он заинтересован в том, чтобы в Зону '
                          f'приходили новые сталкеры 👶. Распространяй информацию о Зоне с помощью этой ссылки {ref_string} '
                          f' 🌎. За каждого нового сталкера Сидорович заплатит тебе {d.SIDOROVICH_BONUS}💰',
                          image=d.SIDOROVICH_PICTURE)
            # if gm_user.ref_src == 'n':
            #     ref_string = f"https://vk.me/public{d.GROUP_BOT_ID}?ref={gm_user.user_id}"
            #     ref_string = d.BH.method('utils.getShortLink', {'url': ref_string})
            #     ref_string = ref_string['short_url']
            #     gm_user.update_database_value(cursor, d.PLAYER_REF_SRC, ref_string)
            # else:
            #     ref_string = gm_user.ref_src
            # blasthack(gm_user,
            #           f'🗺 На кордоне есть торговец по имени Сидорович 👴. Он заинтересован в том, чтобы в Зону '
            #           f'приходили новые сталкеры 👶. Распространяй информацию о Зоне с помощью этой ссылки {ref_string} '
            #           f' 🌎. За каждого нового сталкера Сидорович заплатит тебе {d.SIDOROVICH_BONUS}💰',
            #           image=d.SIDOROVICH_PICTURE)
        elif protomes in d.KEYBOARD_SALES[2].lower():
            blasthack(gm_user, d.ANSWER_IF_NOT_READY)
        else:
            fail_message(gm_user)
        return

    # ----------------------------------------------------------------------------------------------------------------

    # Выбор босса -----------------------------------------------------------------------------------------------------
    elif gm_user.keyboard == d.KEYBOARD_BOSS_SELECT[0]:
        if message in d.KEYBOARD_INVENTORY_ANSWERS[1:-1]:
            data = gm_user.get_boss_date(message, cursor)
            if data == d.ERROR:
                blasthack(gm_user, '❌ Не удалось найти выбранного босса')
                return
            inline_keyboard_specifik(gm_user, data[1], d.KEYBOARD_BOSS_FIGHT_PREPARATION, d.MESSAGE_FLAG_NO_LINE,
                                     data[0])
        else:
            blasthack(gm_user, d.DEFAULT_BOT_ANSWER)
        return

    # атаковать босса и взаимодействие со своей группой
    elif gm_user.keyboard == d.KEYBOARD_BOSS_FIGHT_PREPARATION[0]:
        if protomes in d.KEYBOARD_BOSS_FIGHT_PREPARATION[1].lower():
            data = gm_user.get_user_group(cursor)
            if data == d.PLAYER_NOT_HAVE_GROUP_ERROR:
                inline_keyboard(gm_user, '❌ Ты не состоишь в группе', d.KEYBOARD_BOSS_GROUP_FALSE)
                return
            elif data == d.ERROR:
                blasthack(gm_user, '❌ Группа не найдена, обратитесь к администратору')
                return
            numbers_keyboard(gm_user, data[0], 1, data[1], d.KEYBOARD_BOSS_GROUP_TRUE, key_num=d.KEYBOARD_BOSS_GROUP_TRUE[0])
            gm_user.keyboard = d.KEYBOARD_BOSS_GROUP_TRUE[0]
        elif protomes in d.KEYBOARD_BOSS_FIGHT_PREPARATION[2].lower():
            if gm_user.energy < d.BOSS_FIGHT_PRICE:
                blasthack(gm_user, '❌ Недостаточно энергии для боя с боссом')
                return
            data = gm_user.init_boss_fight(connect)
            if data == d.SUCCESSFUL:
                blasthack(gm_user, '💀 Бой скоро начнётся')
                return
            elif data == d.NEED_MORE_MONEY_ERROR:
                blasthack(gm_user, '❌ У одного из участников группы нехватает энергии для боя с боссом')
                return
            elif data == d.ERROR:
                blasthack(gm_user, '❌ Босс не найден')
                return
            elif data == d.TIMEOUT_ERROR:
                blasthack(gm_user, '❌ Ваша группа недавно создавала заявку')
            else:
                blasthack(gm_user, '♻ Заявка на бой создана. Ожидаю согласия других участников вашей группы')
                for player in data[0]:
                    inline_keyboard_specifik(player, f'❓ Игрок {gm_user.src_name} '
                                                     f'хочет сразиться с боссом {data[1]}. Участвуешь?',
                                             d.KEYBOARD_GROUP_WAIT_BOSS_FIGHT, d.MESSAGE_FLAG_NO_LINE)

        else:
            fail_message(gm_user)
        return

    # создать группу или вступить в существующую (боссы и арена)
    elif gm_user.keyboard == d.KEYBOARD_BOSS_GROUP_FALSE[0] or gm_user.keyboard == d.KEYBOARD_BOSS_GROUP_TRUE[0]:
        if message in d.EMOJI_NUMBER_ASSOTIATIONS:
            res = critter_timeout(gm_user, current_time)
            if res:
                blasthack(gm_user, res)
                return
            target = gm_user.get_group_player_from_number(message, cursor, connect)
            if not target:
                blasthack(gm_user, '❌ Игрок не найден')
                return
            result = target.get_player_data()
            d.MY_STALKER_QUEUE.put([gm_user, result, target])
            thrEvent.set()
            # threading.Thread(target=send_critter_data,
            #                  args=(
            #                      gm_user, result, target)).start()  # затратна по времени, требуется отдельный поток
        elif protomes in d.KEYBOARD_BOSS_GROUP_FALSE[1].lower():
            for player in d.auto_find_group:
                if player.user_id == gm_user.user_id:
                    player.send_message('❌ Ты уже в очереди')
                    return
            group = gm_user.get_group_object(connect)
            if group and len(group) == 3:
                blasthack(gm_user, '❌ В вашей группе максимальное количество участников')
                return
            blasthack(gm_user, '✏ Введи ссылку на пользователя')
            gm_user.keyboard = d.KEYBOARD_GROUP_WAIT_USER_SOURCE[0]
        elif protomes in d.KEYBOARD_BOSS_GROUP_FALSE[2].lower():
            if gm_user.group_id:
                blasthack(gm_user, '❌ Ты уже состоишь в группе')
                return
            data = gm_user.find_group(connect)
            if data == d.SUCCESSFUL:
                blasthack(gm_user, '👥 Ты записался в очередь на поиск группы')
        elif protomes in d.KEYBOARD_BOSS_GROUP_TRUE[2].lower():
            if not gm_user.group_id:
                blasthack(gm_user, '❌ Ты не состоишь в группе')
                return
            data = gm_user.leave_from_group(connect)
            if data == d.ERROR:
                blasthack(gm_user, '❌ Произошла ошибка, обратитесь к администратору')
                return
            blasthack(gm_user, '🚫 Ты вышел из группы')
        else:
            blasthack(gm_user, d.DEFAULT_BOT_ANSWER)
        return

    # запрос игрокам на добавление в команду (арена и боссы)
    elif gm_user.keyboard == d.KEYBOARD_GROUP_WAIT_USER_SOURCE[0] or gm_user.keyboard == \
            d.KEYBOARD_ARENA_WAIT_USER_SOURCE[0]:
        is_arena = True if gm_user.keyboard == d.KEYBOARD_ARENA_WAIT_USER_SOURCE[0] else False
        if 'vk.com/' in message:
            screen_name = message.split('/')[-1]
            d.MESSAGES_QUEUE.put(['users.get', {'user_ids': screen_name}, gm_user.user_id, is_arena])
            # _id = d.BH.method('users.get', {'user_ids': screen_name})
            # if not _id:
            #     blasthack(gm_user, '❌ неправильная ссылка')
            #     return
            # else:
            #     _id = _id[0]['id']
            #     if gm_user.user_id == _id:
            #         blasthack(gm_user, '❌ Нельзя приглашать самого себя')
            #         return
            #     data = gm_user.follow_user_to_group(_id, cursor, is_arena)
            #     if data == d.NEED_MORE_MONEY_ERROR:
            #         blasthack(gm_user, '❌ У приглашённого игрока недостаточно энергии для арены')
            #         return
            #     if data == d.PLAYER_NOT_FOUND_ERROR:
            #         blasthack(gm_user, '❌ Этот пользователь не зарегистрирован в игре')
            #         return
            #     elif data == d.ERROR:
            #         err_ans = 'сражается на арене' if is_arena else 'состоит в команде'
            #         blasthack(gm_user, f'❌ Этот пользователь уже {err_ans} или приглашен другим игроком')
            #         return
            #     elif data == d.SLOT_IS_BUSY_ERROR:
            #         blasthack(gm_user, f'❌ Сначала ответь на последнее приглашение')
            #         return
            #     elif data == d.NO_STACK_ERROR:
            #         blasthack(gm_user, f'❌ Ты уже пригласил другого игрока, подожди ответа')
            #         return
            #     inl_ans = 'на арену' if is_arena else 'в команду'
            #     err = inline_keyboard(data, f'❓ Игрок {gm_user.src_name} пригласил тебя '
            #                                 f'{inl_ans}',
            #                           d.KEYBOARD_ARENA_WAIT_FOLLOW_ANSWER if is_arena else d.KEYBOARD_GROUP_WAIT_FOLLOW_ANSWER)
            #     if err == d.MESSAGE_SEND_ERROR:
            #         blasthack(gm_user, '❌ Этот пользователь запретил отправлять ему сообщения')
            #         return
            #     blasthack(gm_user, f'♻ Ты отправил приглашение игроку {data.src_name}')
            #     return
        else:
            blasthack(gm_user, '❌ неправильная ссылка')
            return

    # Вступление в группу или отказ
    elif gm_user.keyboard == d.KEYBOARD_GROUP_WAIT_FOLLOW_ANSWER[0]:
        if protomes in d.KEYBOARD_GROUP_WAIT_FOLLOW_ANSWER[1].lower():
            data = gm_user.follow_to_group(connect)
            if data == d.ERROR:
                blasthack(gm_user, '❌ Ошибка. Не удалось создать группу')
                return
            blasthack(gm_user, f'Ты вступил в команду {data.src_name}')
            blasthack(data, f'✅ Игрок {gm_user.src_name} принял приглашение')
        elif protomes in d.KEYBOARD_GROUP_WAIT_FOLLOW_ANSWER[2].lower():
            data = gm_user.answer_no_join_group()
            blasthack(gm_user, '❌ Вы отказались от вступления в группу')
            if data:
                blasthack(data, f'❌ Игрок {data.src_name} отказался вступать в группу')
        else:
            fail_message(gm_user)
        return

    # Приглашение на бой с боссом
    elif gm_user.keyboard == d.KEYBOARD_GROUP_WAIT_BOSS_FIGHT[0]:
        if gm_user.fight_ready:
            return
        if message in d.KEYBOARD_GROUP_WAIT_BOSS_FIGHT[1]:
            data = gm_user.check_ready_boss_fight(connect)
            if not data:
                blasthack(gm_user, '❌ Ошибка. Группа не найдена')
                return
            blasthack(gm_user, '✅ Вы приняли приглашение')
            for player in data[0]:
                blasthack(player, f'✅ Игрок {gm_user.src_name} готов к бою')
        elif message in d.KEYBOARD_GROUP_WAIT_BOSS_FIGHT[2]:
            if not gm_user.group_id:
                blasthack(gm_user, '❌ Ты не состоишь в группе')
                return
            group = gm_user.get_group_object(connect)
            group.remove(gm_user)
            d.wait_boss_fight.pop(gm_user.group_id)
            blasthack(gm_user, '❌ Ты отказался от участия в бою')
            for player in group:
                blasthack(player, '❌ Один из игроков отказался, бой с боссом отменён')
        else:
            fail_message(gm_user)
        return

    # ----------------------------------------------------------------------------------------------------------------

    # Арена-----------------------------------------------------------------------------------------------------------
    elif gm_user.keyboard == d.KEYBOARD_ARENA[0]:
        if protomes in d.KEYBOARD_ARENA[1].lower():
            if gm_user.energy < d.ARENA_FIGHT_PRICE:
                blasthack(gm_user, '❌ Недостаточно энергии для арены')
                return
            d.wait_arena_fight.update({gm_user.user_id: gm_user.lvl})
            blasthack(gm_user, '✅ Вы встали в очередь на арену')
        elif protomes in d.KEYBOARD_ARENA[2].lower():
            data = gm_user.get_arena_rating(cursor)
            inline_keyboard(gm_user, data, d.KEYBOARD_SHOW_RATING_CRIT, is_callback=True)
        elif protomes in d.KEYBOARD_ARENA[3].lower():
            if gm_user.energy < d.ARENA_FIGHT_PRICE:
                blasthack(gm_user, '❌ Недостаточно энергии для арены')
                return
            if gm_user.user_id in d.wait_arena_fight:
                blasthack(gm_user, '❌ Вы уже в очереди')
                return
            blasthack(gm_user, '✏ Введи ссылку на пользователя')
            gm_user.keyboard = d.KEYBOARD_ARENA_WAIT_USER_SOURCE[0]
        else:
            fail_message(gm_user)
        return

    # KEYBOARD_ARENA_WAIT_USER_SOURCE лежит там, где боссы в KEYBOARD_GROUP_WAIT_USER_SOURCE

    # Приглашение на арену
    elif gm_user.keyboard == d.KEYBOARD_ARENA_WAIT_FOLLOW_ANSWER[0]:
        if protomes in d.KEYBOARD_ARENA_WAIT_FOLLOW_ANSWER[1].lower():
            data = gm_user.follow_to_arena()
            if data == d.ERROR:
                blasthack(gm_user, '❌ Ошибка. Не удалось начать бой')
                return
            blasthack(gm_user, '✅ Ты принял приглашение, бой скоро начнется')
            blasthack(data, f'✅ Игрок {gm_user.src_name} принял приглашение')
        elif protomes in d.KEYBOARD_ARENA_WAIT_FOLLOW_ANSWER[2].lower():
            data = gm_user.answer_no_join_arena()
            blasthack(gm_user, '❌ Вы отказались от боя на арене')
            if data:
                blasthack(data, f'❌ Игрок {data.src_name} отказался идти на арену')
        else:
            fail_message(gm_user)
        return

    # ---------------------------------------------------------------------------------------------------------------

    # Лут кейсы -----------------------------------------------------------------------------------------------------
    elif gm_user.keyboard == d.KEYBOARD_LOOT[0]:
        if protomes in d.KEYBOARD_LOOT[1].lower():
            res = gm_user.loot_case_open(cursor,
                                         gm_user.get_item_by_pid(d.LOOT_CASE_DEFAULT[0], d.TYPE_LOOT_CASES_ID))
            if res != d.ERROR:
                blasthack(gm_user, res)
            else:
                blasthack(gm_user, '❌ У вас нет кейсов данного типа')
        elif protomes in d.KEYBOARD_LOOT[2].lower():
            if gm_user.balance < d.LOOT_CASE_DEFAULT[1]:
                blasthack(gm_user, '❌ Недостаточно денег для покупки')
                return
            else:
                res = gm_user.loot_case_buy(cursor, d.LOOT_CASE_DEFAULT)
                if res != d.SUCCESSFUL:
                    blasthack(gm_user, '❌ Недостаточно денег для покупки')
                else:
                    blasthack(gm_user, '✅ Вы купили стандартный лут кейс')
        elif protomes in d.KEYBOARD_LOOT[3].lower():
            inline_keyboard(gm_user, '👴 Выбирай', d.KEYBOARD_LOOT_ALL)
        else:
            fail_message(gm_user)
        return

    # Подробный список кейсов
    elif gm_user.keyboard == d.KEYBOARD_LOOT_ALL[0]:
        loot_case_number = 0
        if protomes in d.KEYBOARD_LOOT_ALL[1].lower():
            loot_case_number = d.LOOT_CASE_DEFAULT
        elif protomes in d.KEYBOARD_LOOT_ALL[2].lower():
            loot_case_number = d.LOOT_CASE_HELMETS
        elif protomes in d.KEYBOARD_LOOT_ALL[3].lower():
            loot_case_number = d.LOOT_CASE_ARTEFACTS
        elif protomes in d.KEYBOARD_LOOT_ALL[4].lower():
            loot_case_number = d.LOOT_CASE_UPGRADES
        else:
            blasthack(gm_user, d.DEFAULT_BOT_ANSWER)
            return
        res = gm_user.loot_case_open(cursor, gm_user.get_item_by_pid(loot_case_number[0], d.TYPE_LOOT_CASES_ID))
        if res != d.ERROR:
            blasthack(gm_user, res)
        else:
            blasthack(gm_user, '❌ У вас нет кейсов данного типа')
        return

    # ----------------------------------------------------------------------------------------------------------------

    # Прочее----------------------------------------------------------------------------------------------------------
    elif gm_user.keyboard == d.KEYBOARD_OTHER[0]:
        if not key_num:
            return
        if protomes in d.KEYBOARD_OTHER[1].lower() or key_num % d.PAYLOAD_MULTIPLIER == 0:
            inline_keyboard(gm_user, stalker.get_random_anekdot(), [d.KEYBOARD_OTHER[0], '💥 Ещё'])
        elif protomes in d.KEYBOARD_OTHER[2].lower():
            blasthack(gm_user,
                      '🌄 Стикеры с персонажами Stalker можно скачать тут https://vk.cc/ceHghk . Пароль от архива stalkerbot.',
                      image='photo-210036099_457240198,photo-210036099_457240199,photo-210036099_457240200')
        else:
            blasthack(gm_user, d.DEFAULT_BOT_ANSWER)
        return

    # ----------------------------------------------------------------------------------------------------------------

    # Ссылки ---------------------------------------------------------------------------------------------------------
    # Не сделано
    # ----------------------------------------------------------------------------------------------------------------

    # Донат ----------------------------------------------------------------------------------------------------------
    elif gm_user.keyboard == d.KEYBOARD_DONUT[0]:
        gm_user.buy_info = []
        if protomes in d.KEYBOARD_DONUT[1].lower():
            gm_user.buy_info = d.SHOP_ENERGETIK
        elif protomes in d.KEYBOARD_DONUT[2].lower():
            gm_user.buy_info = d.SHOP_NAEMNIK
        elif protomes in d.KEYBOARD_DONUT[3].lower():
            gm_user.buy_info = d.SHOP_FREDDY
        elif protomes in d.KEYBOARD_DONUT[4].lower():
            cur_src = f'https://vk.com/app6887721_-{d.DONUT_GROUP_ID}#donate_{d.DONUT_PREMIUM[1]}&op_{d.DONUT_PREMIUM[0]}'
            blasthack(gm_user, f'🔥 Цена премиума {d.DONUT_PREMIUM[1]} рублей, оплата через сервис кексик, {cur_src}'
                               f'. После оплаты премиум активируется в течение 10 минут')
            return
        if gm_user.buy_info:
            inline_keyboard(gm_user, f'Цена {gm_user.buy_info[2]}💰', d.KEYBOARD_BUY_ANSWER, gm_user.buy_info[3])
        else:
            fail_message(gm_user)
        return

    elif gm_user.keyboard == d.KEYBOARD_BUY_ANSWER[0]:
        if protomes in d.KEYBOARD_BUY_ANSWER[1].lower():
            price = gm_user.buy_info[2]
            if price > gm_user.balance:
                blasthack(gm_user, '❌ Недостаточно денег')
                return
            if gm_user.buy_info[1] == d.TYPE_REWARDS_SKIN or gm_user.buy_info[1] == d.BIN_TYPE_BACKGROUNDS:
                if gm_user.buy_info[1] == d.TYPE_REWARDS_SKIN:
                    tmp_val = d.BIN_TYPE_SKINS
                else:
                    tmp_val = d.BIN_TYPE_BACKGROUNDS
                if not gm_user.check_bin_param(gm_user.buy_info[0], tmp_val):
                    gm_user.add_bin_param(cursor, gm_user.buy_info[0], tmp_val)
                else:
                    blasthack(gm_user, '❌ У тебя максимальное количество этих предметов')
                    return
            else:
                item = [gm_user.buy_info[0], gm_user.buy_info[1]]
                gm_user.update_user_balance(cursor, -price)
                gm_user.add_item_to_database(item, cursor)
            blasthack(gm_user, '✅ Предмет куплен')
        elif protomes in d.KEYBOARD_BUY_ANSWER[2].lower():
            blasthack(gm_user, '❌ Покупка отменена')
        else:
            fail_message(gm_user)
        return
    # ----------------------------------------------------------------------------------------------------------------

    # Фоны -----------------------------------------------------------------------------------------------------------
    # elif gm_user.keyboard == d.KEYBOARD_BACKGROUNDS[0]:
    #     for i in range(1, len(d.KEYBOARD_BACKGROUNDS)):
    #         if protomes in d.KEYBOARD_BACKGROUNDS[-1].lower():
    #             gm_user.update_database_value(cursor, d.PLAYER_BACKGROUND, 0)
    #             blasthack(gm_user, '✅ Фон был изменён на обычный')
    #             return
    #         elif protomes in d.KEYBOARD_BACKGROUNDS[i].lower():
    #             data = cursor.execute(f"SELECT * from background WHERE background_id = {i}").fetchall()
    #             inline_keyboard(gm_user, None, d.KEYBOARD_BACKGROUNDS_CHOSE, data[0][2])
    #             gm_user.temp_data = [d.TEMP_BACKGROUND_ID_INDEX, i]
    #             return
    #     fail_message(gm_user)
    #     return
    #
    # # Выбрать фон или вернуться
    # elif gm_user.keyboard == d.KEYBOARD_BACKGROUNDS_CHOSE[0]:  # фоны
    #     if not gm_user.temp_data:
    #         return
    #     if gm_user.temp_data[0] != d.TEMP_BACKGROUND_ID_INDEX:
    #         return
    #     background_index = gm_user.temp_data[1]
    #     if protomes in d.KEYBOARD_BACKGROUNDS_CHOSE[1].lower():
    #         gm_user.update_database_value(cursor, d.PLAYER_BACKGROUND, background_index)
    #         gm_user.temp_data = []
    #         blasthack(gm_user, "✅ Фон был изменён")
    #         gm_user.keyboard = d.KEYBOARD_MY_STALKER[0]
    #     elif protomes in d.KEYBOARD_BACKGROUNDS_CHOSE[2].lower():  # cкины
    #         gm_user.temp_data = []
    #         inline_keyboard(gm_user, '🗺 Выбери фон', d.KEYBOARD_BACKGROUNDS)
    #     else:
    #         fail_message(gm_user)
    #     return
    elif gm_user.keyboard == d.KEYBOARD_BACKGROUNDS[0]:
        if not key_num:
            blasthack(gm_user, '❌ Используй кнопки')
            return
        skin_num = key_num % d.PAYLOAD_MULTIPLIER
        if not (skin_num == 0) and not gm_user.check_bin_param(skin_num, d.BIN_TYPE_BACKGROUNDS):
            blasthack(gm_user, '❌ Фон недоступен')
            return
        if skin_num == 0:
            gm_user.update_database_value(cursor, d.PLAYER_BACKGROUND, skin_num)
            blasthack(gm_user, '✅ Фон изменён')
            gm_user.img_ready = False
            return
        keyboard = VkKeyboard(inline=True)
        keyboard.add_button(d.KEYBOARD_BACKGROUNDS_CHOSE[1], color=VkKeyboardColor.PRIMARY,
                            payload=(d.KEYBOARD_BACKGROUNDS_CHOSE[0] * d.PAYLOAD_MULTIPLIER + skin_num))
        keyboard.add_button(d.KEYBOARD_SKINS_SELECT[2], color=VkKeyboardColor.PRIMARY,
                            payload=(d.KEYBOARD_MY_STALKER[0] * d.PAYLOAD_MULTIPLIER))
        cursor.execute(f'SELECT source from background WHERE background_id = {skin_num}')
        att = cursor.fetchall()[0][0]
        att = d.DEFAULT_PICTURE_VK if att == 'n' else att
        gm_user.send_message(None, keyboard.get_keyboard(), att)
        return

    elif gm_user.keyboard == d.KEYBOARD_BACKGROUNDS_CHOSE[0]:
        if not key_num:
            blasthack(gm_user, '❌ Используй кнопки')
            return
        skin_num = key_num % d.PAYLOAD_MULTIPLIER
        if not (skin_num == 0) and not gm_user.check_bin_param(skin_num, d.BIN_TYPE_BACKGROUNDS):
            blasthack(gm_user, '❌ Фон недоступен')
            return
        gm_user.update_database_value(cursor, d.PLAYER_BACKGROUND, skin_num)
        blasthack(gm_user, '✅ Фон изменён')
        gm_user.img_ready = False
        return
    # ----------------------------------------------------------------------------------------------------------------

    # Скины ----------------------------------------------------------------------------------------------------------
    elif gm_user.keyboard == d.KEYBOARD_SKINS[0]:
        if not key_num:
            blasthack(gm_user, '❌ Используй кнопки')
            return
        skin_num = key_num % d.PAYLOAD_MULTIPLIER
        if not (skin_num == 0) and not gm_user.check_bin_param(skin_num, d.BIN_TYPE_SKINS):
            blasthack(gm_user, '❌ Скин недоступен')
            return
        keyboard = VkKeyboard(inline=True)
        keyboard.add_button(d.KEYBOARD_SKINS_SELECT[1], color=VkKeyboardColor.PRIMARY,
                            payload=(d.KEYBOARD_SKINS_SELECT[0] * d.PAYLOAD_MULTIPLIER + skin_num))
        keyboard.add_button(d.KEYBOARD_SKINS_SELECT[2], color=VkKeyboardColor.PRIMARY,
                            payload=(d.KEYBOARD_MY_STALKER[0] * d.PAYLOAD_MULTIPLIER + 1))
        cursor.execute(f'SELECT source from skins WHERE skin_id = {skin_num}')
        att = cursor.fetchall()[0][0]
        att = d.DEFAULT_PICTURE_VK if att == 'n' else att
        gm_user.send_message(None, keyboard.get_keyboard(), att)
        return

    elif gm_user.keyboard == d.KEYBOARD_SKINS_SELECT[0]:
        if not key_num:
            blasthack(gm_user, '❌ Используй кнопки')
            return
        skin_num = key_num % d.PAYLOAD_MULTIPLIER
        if not (skin_num == 0) and not gm_user.check_bin_param(skin_num, d.BIN_TYPE_SKINS):
            blasthack(gm_user, '❌ Скин недоступен')
            return
        gm_user.update_database_value(cursor, d.PLAYER_SKIN, skin_num)
        blasthack(gm_user, '✅ Скин изменён')
        gm_user.img_ready = False
        return
    # ----------------------------------------------------------------------------------------------------------------

    # Эвенты ----------------------------------------------------------------------------------------------------------
    elif gm_user.keyboard == d.KEYBOARD_EVENT1[0]:
        if protomes in d.KEYBOARD_EVENT1[1].lower():
            if not gm_user.check_bin_param(d.GAME_EVENT_TEST, d.BIN_TYPE_EVENTS):
                blasthack(gm_user, d.DEFAULT_BOT_EVENT_ANSWER)
                return
            gm_user.update_user_balance(cursor, 5000)
            blasthack(gm_user, f'✅ Получено 5000💰, баланс {gm_user.balance}💰')
            gm_user.remove_bin_param(cursor, d.GAME_EVENT_TEST, d.BIN_TYPE_EVENTS)
        return

    elif gm_user.keyboard == d.KEYBOARD_EVENT2[0]:
        if protomes in d.KEYBOARD_EVENT2[1].lower():
            if not gm_user.check_bin_param(d.GAME_EVENT_TEST2, d.BIN_TYPE_EVENTS):
                blasthack(gm_user, d.DEFAULT_BOT_EVENT_ANSWER)
                return
            gm_user.add_item_to_database(d.ARMOR_DOLG, cursor)
            blasthack(gm_user, f'✅ Получен предмет Броня долга')
            gm_user.remove_bin_param(cursor, d.GAME_EVENT_TEST2, d.BIN_TYPE_EVENTS)
        return

    elif gm_user.keyboard == d.KEYBOARD_EVENT3[0]:
        if protomes in d.KEYBOARD_EVENT3[1].lower():
            gm_user.add_bin_param(cursor, 2, d.BIN_TYPE_SKINS)
            blasthack(gm_user, '✅ Получен скин наёмника')
        elif protomes in d.KEYBOARD_EVENT3[2].lower():
            gm_user.add_bin_param(cursor, 2, d.BIN_TYPE_BACKGROUNDS)
            blasthack(gm_user, '✅ Получен фон мишк Фредди')
        return

    elif gm_user.keyboard == d.KEYBOARD_EVENT_VIPE[0]:
        if protomes in d.KEYBOARD_EVENT_VIPE[1].lower():
            if not gm_user.check_bin_param(d.GAME_EVENT_VIPE, d.BIN_TYPE_EVENTS):
                blasthack(gm_user, d.DEFAULT_BOT_EVENT_ANSWER)
                return
            mods = 0b111
            gm_user.add_item_to_database(d.ARMOR_BULAT, cursor, mods=mods)
            gm_user.add_item_to_database(d.WEAPON_SHTORM, cursor, mods=mods)
            gm_user.add_item_to_database(d.WEAPON_OHOTKA, cursor, mods=mods)
            gm_user.update_user_balance(cursor, + 10000)
            blasthack(gm_user, f'✅ Получено: Булат, Шторм, Охотничье ружьё, 10000💰.')
            gm_user.remove_bin_param(cursor, d.GAME_EVENT_VIPE, d.BIN_TYPE_EVENTS)
        return

    elif gm_user.keyboard == d.KEYBOARD_EVENT_CLEAR_SKY[0]:
        if protomes in d.KEYBOARD_EVENT_CLEAR_SKY[1].lower():
            if not gm_user.check_bin_param(d.GAME_EVENT_CLEAR_SKY, d.BIN_TYPE_EVENTS):
                blasthack(gm_user, d.DEFAULT_BOT_EVENT_ANSWER)
                return
            gm_user.add_bin_param(cursor, 4, d.BIN_TYPE_SKINS)
            blasthack(gm_user, '✅ Получен скин чистое небо')
            gm_user.remove_bin_param(cursor, d.GAME_EVENT_CLEAR_SKY, d.BIN_TYPE_EVENTS)
        return
    # ----------------------------------------------------------------------------------------------------------------

    else:  # Если ничего не подошло
        fail_message(gm_user)
        return


# except Exception as e:
#     for frame in traceback.extract_tb(sys.exc_info()[2]):
#         fname, lineno, fn, text = frame
#         print(f"{e} in %s on line %d" % (fname, lineno))


# Слушаем longpoll(Сообщения)
def main_function():
    while True:
        try:
            for event in d.LONGPOLL.listen():
                if event.type == VkBotEventType.MESSAGE_NEW or event.type == VkBotEventType.MESSAGE_EVENT:  # VkEventType.MESSAGE_NEW:
                    # cur_time = time.time()
                    # Чтобы наш бот не слышал и не отвечал на самого себя
                    message = ''
                    _id = 0
                    if event.type == VkBotEventType.MESSAGE_NEW:
                        if event.from_user:
                            d.CURRENT_PEER_ID = 0
                            message = event.object.text
                        elif event.from_chat:
                            d.CURRENT_PEER_ID = event.object.peer_id
                            if f'@public{d.GROUP_BOT_ID}' in event.object.text:
                                message = event.object.text[d.GROUP_BOT_ID_LEN:]
                            elif f'@club{d.GROUP_BOT_ID}' in event.object.text:
                                message = event.object.text[d.GROUP_BOT_ID_LEN - 2:]
                            elif d.GROUP_NAME in event.object.text:
                                message = event.object.text[len(d.GROUP_NAME):]
                            elif d.GROUP_BOT_NAME in event.object.text.lower():
                                message = event.object.text[len(d.GROUP_BOT_NAME) + 1:]
                            else:
                                continue
                        else:
                            continue
                        if len(message) < 1:
                            continue
                        _id = event.object.from_id
                    elif event.type == VkBotEventType.MESSAGE_EVENT:
                        message = 'never'
                        if event.object.user_id != event.object.peer_id:
                            d.CURRENT_PEER_ID = event.object.peer_id
                        _id = event.object.user_id
                        # try:
                        d.MESSAGES_QUEUE.put(['messages.sendMessageEventAnswer',
                                              {'event_id': event.object.event_id,
                                               'user_id': _id,
                                               'peer_id': d.CURRENT_PEER_ID if d.CURRENT_PEER_ID != 0 else _id}])
                            # d.GIVE.messages.sendMessageEventAnswer(
                            #     event_id=event.object.event_id,
                            #     user_id=_id,
                            #     peer_id=(
                            #         d.CURRENT_PEER_ID if d.CURRENT_PEER_ID != 0 else _id))
                        # except vk_api.exceptions.ApiError:
                        #     pass
                    if _id in d.active_users:  # Пользователь зарегистрирован и недавно играл
                        player = d.get_player(_id)
                        what_message(player, message, event.object.payload)
                    else:
                        player = None
                        cursor.execute('SELECT * FROM users')
                        for row in cursor:
                            if row[0] == _id:  # Пользователь зарегистрирован
                                player = stalker.Stalker(_id, cursor, False)
                                connect.commit()
                                what_message(player, message, event.object.payload)
                                break
                        if not player:  # Пользователь новичок
                            if event.object.ref:  # награда за рефералку
                                stalker.sidorovich_reward(_id, event.object.ref, cursor)
                            player = stalker.Stalker(_id, cursor, True)
                            connect.commit()
                            what_message(player, message, event.object.payload)
                    connect.commit()
                    player.connect_time = time.time()  # обновление времени, чтобы не удаляло активных игроков каждые 20 минут
                    while None in player.items:
                        player.items.remove(None)
                    # print(time.time()-cur_time)
        except exceptions.ConnectionError:
            d.restart_connection()
            continue
        except exceptions.ReadTimeout:
            d.restart_connection()
            continue


main_function()
