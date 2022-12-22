"""
Базовый конфиг для игры Stalker bot. Здесь хранятся различные токены, данные авторизации и ссылки на группы
"""

GameDebug = True  # если включён, то программа будет использовать альтернативную группу для работы бота
VkBotToken = "" if not GameDebug \
    else ""
GroupBotName = "сталкер"  # имя, на которое будет отзываться бот в беседах при наличии у него админки
VkGroupId = "" if not GameDebug else ""
GroupName = f'[club{VkGroupId}|STALKER BOT (beta)]' if not GameDebug else f'[club{VkGroupId}|bottest]'
ApiVersion = '5.92'

DonutIsWork = False
DonutGroupId = ""  # группа, к которой подключён кексик
DonutToken = ""

DatabaseInfo = {"dbname": "stalker", "user": "postgres", "password": "k14ca9jhD", "host": "localhost"}