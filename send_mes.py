import sqlite3
import psycopg2
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

import defines as d
import time
import vk_api

"""Рассылка сообщений для игроков. Самое то для эвентов и рекламы. 
Автоматически выполняется при запуске бота, если включён флаг SEND_EVENT в defines.py"""


def go_send_mes():
    offset = 100
    # connect = sqlite3.connect('BotStalker.db')
    connect = psycopg2.connect(dbname=d.DATABASE_INFO["dbname"], user=d.DATABASE_INFO["user"],
                               password=d.DATABASE_INFO["password"], host=d.DATABASE_INFO["host"])
    cursor = connect.cursor()
    cursor.execute('SELECT COUNT(user_id) from users')
    count = cursor.fetchall()[0][0]

    # /////////////////////////////////////////////////////////////////////////////
    sendMSG = ['🔥 В группе появились обсуждения игровых багов и предложений по улучшению бота https://vk.com/board210036099 .\n Альфа версия игры уже не за горами :)']
    # attPATH = 'attachment/send.png'
    attPATH = [None]  # взаимоисключается с attach_source
    attach_source = ['photo-213053803_457240312']
    keyb = [d.KEYBOARD_EVENT_CLEAR_SKY]
    # ////////////////////////////////////////////////////////////////////////////

    for k in range(len(sendMSG)):
        if attPATH[k]:
            upload = vk_api.VkUpload(d.GIVE)
            photo = upload.photo_messages(attPATH[k])
            owner_id = photo[0]['owner_id']
            photo_id = photo[0]['id']
            access_key = photo[0]['access_key']
            attachment = f'photo{owner_id}_{photo_id}_{access_key}'
        else:
            attachment = None

        if not attachment and attach_source[k]:
            attachment = attach_source[k]

        if keyb[k]:
            keyboard = VkKeyboard(inline=True)
            for i in range(1, len(keyb[k])):
                if keyb[k][i] is None:
                    continue
                keyboard.add_button(keyb[k][i], color=VkKeyboardColor.PRIMARY,
                                    payload=f'{keyb[k][0] * d.PAYLOAD_MULTIPLIER + i - 1}')
            keyboard = keyboard.get_keyboard()
        else:
            keyboard = None

        for i in range(max(count//offset, 1)):
            ids = []
            cursor.execute(f'SELECT user_id from users LIMIT {offset} OFFSET {offset*i}')
            data = cursor.fetchall()
            try:
                for j in range(offset):
                    ids.append(data[j][0])
            except IndexError:
                pass
            try:
                d.GIVE.messages.send(peer_ids=ids,
                                     message=sendMSG[k],
                                     random_id=int(time.time() * 1000000),
                                     keyboard=keyboard,
                                     attachment=attachment)
            except vk_api.exceptions.ApiError:
                pass


if __name__ == '__main__':
    go_send_mes()
