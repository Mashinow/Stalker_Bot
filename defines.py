import vk_api
from vk_api.bot_longpoll import VkBotLongPoll
from random import choice
import game_config as gc
from queue import Queue

"""
Здесь хранятся игровые константы, тексты сообщений от бота и некоторые общие функции
"""

""" 
[id{gm_user.user_id}|{gm_user.user_name}]
Часто используемые смайлики:
💵 доллары
➕ рост
➖ падение
👥 группа
👤 юзер
⌛ (песочные часы) кулдауны
🚫 выход
❓ вопрос
♻ ожидание
❌ err
✅ yes
🛠 (инструменты) - ещё не готово
🔥 (огонь) - акции итд
🤝 (рукопожатие) акции
🔎 (лупа) - поиск чего-либо
💰 (деньги) - торговля
🎰 (казино) - мини игры
🕹 (джойстик) - мини игры
🎮 (джойстик2) - мини игры
🎯 (мишень)
🍺 (пиво) - бар
⚖ (весы) - аукцион
💼 (портфель) - инвентарь и лут кейсы
🐲 (дракон) - боссы
⚔ (мечи) - пвп
🎁 (подарок) - лут кейсы и подарки
🗺 (карта) - локации
🌄 (пейзаж) - фон
🎭 (маски) - скины
🔮 (сфера) - навыки
🏆 (кубок) - рейтинг
🆘 (sos) - помощь
👷 (работяга) - работа
🎒 (рюкзак2) - открытие кейсов
🏧 (atm) - донат
🏪 (магазиг)
🤑 (смайл с долларами в глазах)
🌎 (планета)
👴 (лысый чел) - сидорович
✏ (карандаш) 👖 (штаны) 💀 (череп) ✍ (рука пишущая) ✉ (письмо) 📈 (торговля)
сигнатуры
📋 (блокнот) - ник; 🔪 (нож) - урон; 🎲 (кости) - любой рандом; 🛡 (щит) - защита
❤ Регенерация', '🆙 Бонус к здоровью', '
типы урона
⚡ Электро', '👊 Удар', '💢 Разрыв', '☢ Радиация', '☣ Хим. Ожог', '💥 Взрыв', '🔫 Норма
предметы
🔫' пистолеты, '👔'броня, '🔮'артефакты, '👒'шлемы, '🎁'кейсы, '⚙ улучшения ❣ Здоровье
"""

# DEBUG = True
SEND_EVENT = False
TOKEN = gc.VkBotToken
GROUP_BOT_NAME = 'сталкер'
GROUP_BOT_ID = gc.VkGroupId
GROUP_NAME = gc.GroupName
DONUT_WORK = gc.DonutIsWork
DONUT_TOKEN = gc.DonutToken
DONUT_GROUP_ID = gc.DonutGroupId
DATABASE_INFO = gc.DatabaseInfo
GROUP_BOT_ID_LEN = len(GROUP_NAME)+len(GROUP_BOT_ID)+1
BH = vk_api.VkApi(token=TOKEN, api_version=gc.ApiVersion)
GIVE = BH.get_api()
LONGPOLL = VkBotLongPoll(vk=BH, group_id=int(GROUP_BOT_ID))
MSG_POOL = vk_api.VkRequestsPool(BH)
active_users = []  # массив с идентификаторами активных пользователей
player_objects = []  # массив с объектами активных пользователей

MESSAGES_QUEUE = Queue()

combat_objects = []  # массив с объектами текущих боёв
# combat_game_tick = 0  # время для тиков боя, обновляется внешне
COMBAT_GAME_TICK = 5  # длительность хода
EVENTS_GAME_TICK = 300  # проверка событий
PAYLOAD_MULTIPLIER = 100  # на что умножается номер клавы для кнопок
LAST_BONUS_DAY = 0  # защита от повторной выдачи лут кейсов
Global_Item_Id = 50  # идентификатор последнего сгенерированного итема
Global_Group_Id = 1
wait_group_follow = []  # формат: [(пригласивший, приглашённый, время создания)]
wait_arena_follow = []
auto_find_group = []  # пати на боссов
wait_boss_fight = {}  # формат: {group_id:[selected_boss, time.time()]}
wait_arena_fight = {}  # очередь на арену, формат {player.user_id: player.lvl}
CURSOR = None
CONNECT = None
# wait_autorization = {}  # очередь на авторизацию, формат {id:[first, message]}


# items max id кроме кейсиков. НЕ УЧИТЫВАЕТ РЕДКИЕ ПРЕДМЕТЫ (ИХ ПИД ПРЕВЫШАЕТ 100)
START_RARE_ITEMS_PROTO = 100  #

LAST_PROTO_ARMOR = 0  # сами по себе бесполезны, используются как имена для списка
LAST_PROTO_ARTEFACT = 0
LAST_PROTO_WEAPON = 0
LAST_PROTO_HELMET = 0
LAST_PROTO_MOD_WEAPON = 0
LAST_PROTO_MOD_ARMOR = 0
LAST_PROTO_MOD_HELMET = 0

# Item_type
TYPE_WEAPONS_ID = 1
TYPE_ARMOR_ID = 2
TYPE_ARTEFACTS_ID = 3
TYPE_HELMETS_ID = 4
TYPE_LOOT_CASES_ID = 5
TYPE_UPGRADES_WEAPON_ID = 6
TYPE_UPGRADES_ARMOR_ID = 7
TYPE_UPGRADES_HELMET_ID = 8
TYPE_USE_ITEMS = 9

# ///////////////////////////////////// все дефайны в этом сегменте используются как награды с боссов итд
# weapons
WEAPON_KORA909 = (1, TYPE_WEAPONS_ID)
WEAPON_SIP200 = (2, TYPE_WEAPONS_ID)
WEAPON_OHOTKA = (3, TYPE_WEAPONS_ID)
WEAPON_SHTORM = (101, TYPE_WEAPONS_ID)
WEAPON_FT200 = (102, TYPE_WEAPONS_ID)
WEAPON_GAUSS = (103, TYPE_WEAPONS_ID)

# armor defines
ARMOR_BANDIT_JACKET = (1, TYPE_ARMOR_ID)
ARMOR_NAEMNIK = (2, TYPE_ARMOR_ID)
ARMOR_SEVA = (3, TYPE_ARMOR_ID)
ARMOR_DOLG = (4, TYPE_ARMOR_ID)
ARMOR_BULAT = (101, TYPE_ARMOR_ID)
ARMOR_EXOSKELET_DOLG = (102, TYPE_ARMOR_ID)
ARMOR_EXOSKELET_SVOBODA = (103, TYPE_ARMOR_ID)
ARMOR_BERILL = (104, TYPE_ARMOR_ID)

# artefacts defines
ARTEFACT_SOUL = (1, TYPE_ARTEFACTS_ID)
ARTEFACT_KOLOBOK = (2, TYPE_ARTEFACTS_ID)
ARTEFACT_BLOODSTONE = (3, TYPE_ARTEFACTS_ID)
ARTEFACT_FLAME = (101, TYPE_ARTEFACTS_ID)
ARTEFACT_OAZIS = (102, TYPE_ARTEFACTS_ID)
ARTEFACT_KOMPAS = (103, TYPE_ARTEFACTS_ID)

# helmets defines
HELMET_ZASLON = (1, TYPE_HELMETS_ID)
HELMET_TACTICAL = (2, TYPE_HELMETS_ID)
HELMET_SFERAM12 = (101, TYPE_HELMETS_ID)

# upgrade weapons
MOD_W_STVOL = (1, TYPE_UPGRADES_WEAPON_ID, 1)
MOD_W_ZATVOR = (2, TYPE_UPGRADES_WEAPON_ID, 1)
MOD_POLIMER_DET = (17, TYPE_UPGRADES_WEAPON_ID, 1)
# upgrade armor
MOD_EKRAN_ARM = (17, TYPE_UPGRADES_ARMOR_ID, 1)
# upgrade helmets
MOD_EKRAN_HELM = (17, TYPE_UPGRADES_HELMET_ID, 1)

# loot_case_reward
REWARD_CASE_DEFAULT = (1, TYPE_LOOT_CASES_ID, 1)
REWARD_CASE_HELMETS = (2, TYPE_LOOT_CASES_ID, 1)
REWARD_CASE_ARTEFACTS = (3, TYPE_LOOT_CASES_ID, 1)
REWARD_CASE_UPGRADES = (4, TYPE_LOOT_CASES_ID, 1)

# skin reward
TYPE_REWARDS_SKIN = 501
REWARD_SKIN_BANDIT = (1, TYPE_REWARDS_SKIN, 'Бандита')

# background reward
TYPE_REWARDS_BACKGROUND = 502
REWARD_BACKGROUND_FALLOUT = (3, TYPE_REWARDS_BACKGROUND, 'Fallout')
# /////////////////////////////////////


# loot cases
LOOT_CASE_REWARD_TYPES = {TYPE_WEAPONS_ID: LAST_PROTO_WEAPON, TYPE_ARMOR_ID: LAST_PROTO_ARMOR,
                          TYPE_ARTEFACTS_ID: LAST_PROTO_ARTEFACT, TYPE_HELMETS_ID: LAST_PROTO_HELMET,
                          TYPE_UPGRADES_ARMOR_ID: LAST_PROTO_MOD_ARMOR, TYPE_UPGRADES_HELMET_ID: LAST_PROTO_MOD_HELMET,
                          TYPE_UPGRADES_WEAPON_ID: LAST_PROTO_MOD_WEAPON}
LOOT_CASE_DEFAULT = [1, 2000, [TYPE_WEAPONS_ID, TYPE_ARMOR_ID]]
LOOT_CASE_HELMETS = [2, 1000, [TYPE_HELMETS_ID]]
LOOT_CASE_ARTEFACTS = [3, 1000, [TYPE_ARTEFACTS_ID]]
LOOT_CASE_UPGRADES = [4, 2000, [TYPE_UPGRADES_WEAPON_ID, TYPE_UPGRADES_HELMET_ID, TYPE_UPGRADES_ARMOR_ID]]

ALL_LOOT_CASES = ['ERR', LOOT_CASE_DEFAULT, LOOT_CASE_HELMETS, LOOT_CASE_ARTEFACTS, LOOT_CASE_UPGRADES]

# имена всех типов
TYPE_WEAPONS_NAME = 'weapons'
TYPE_ARMOR_NAME = 'armors'
TYPE_ARTEFACTS_NAME = 'artefacts'
TYPE_HELMETS_NAME = 'helmets'
TYPE_LOOT_CASES_NAME = 'loot_cases'
TYPE_UPGRADES_WEAPON_NAME = 'upgrades_weapon'
TYPE_UPGRADES_ARMOR_NAME = 'upgrades_armor'
TYPE_UPGRADES_HELMET_NAME = 'upgrades_helmet'
TYPE_USE_ITEMS_NAME = 'use_items'

# TYPE_NAME_ITEM_ASSOTIATIONS = {TYPE_WEAPONS_ID: TYPE_WEAPONS_NAME, TYPE_ARMOR_ID: TYPE_ARMOR_NAME,
# TYPE_ARTEFACTS_ID: TYPE_ARTEFACTS_NAME, TYPE_HELMETS_ID: TYPE_HELMETS_NAME, TYPE_LOOT_CASES_ID: TYPE_LOOT_CASES_NAME,
# TYPE_UPGRADES_WEAPON_ID: TYPE_UPGRADES_WEAPON_NAME, TYPE_UPGRADES_ARMOR_ID: TYPE_UPGRADES_ARMOR_NAME,
# TYPE_UPGRADES_HELMET_ID: TYPE_UPGRADES_HELMET_NAME}


# данные для отрисовки характеристик выбранного предмета в инвентаре
WEAPONS_SIGNATURE = ['📋 Имя', '⚔ Тип урона', '🔪 Урон', '🎲 Шанс на крит', '🎲 Шанс на попадание', '💢 Пробивание',
                     '💰 Цена']
ARMORS_SIGNATURE = ['📋 Имя', '🛡 Защита', '⚡ Электро', '👊 Удар', '💢 Разрыв', '☢ Радиация', '☣ Хим. Ожог', '💥 Взрыв',
                    '🔫 Норма', '❤ Регенерация', '🆙 Бонус к здоровью', '🎲 Уворот', '💰 Цена']
ARTEFACTS_SIGNATURE = ARMORS_SIGNATURE
HELMETS_SIGNATURE = ARMORS_SIGNATURE
LOOT_CASES_SIGNATURE = ['📋 Имя', '💰 Цена']
UPGRADES_WEAPON_SIGNATURE = WEAPONS_SIGNATURE
UPGRADES_ARMOR_SIGNATURE = ARMORS_SIGNATURE
UPGRADES_HELMET_SIGNATURE = HELMETS_SIGNATURE
USE_ITEMS_SIGNATURE = LOOT_CASES_SIGNATURE
ALL_ITEM_SIGNATURES = ['ERROR', WEAPONS_SIGNATURE, ARMORS_SIGNATURE, ARTEFACTS_SIGNATURE, HELMETS_SIGNATURE,
                       LOOT_CASES_SIGNATURE, UPGRADES_WEAPON_SIGNATURE, UPGRADES_ARMOR_SIGNATURE,
                       UPGRADES_HELMET_SIGNATURE, USE_ITEMS_SIGNATURE]

ITEMS_SALE_PENALTY = 10  # коэффициент на который будет делиться цена товара при продаже

ITEMS_CAN_PUT = [TYPE_WEAPONS_ID, TYPE_ARMOR_ID, TYPE_ARTEFACTS_ID, TYPE_HELMETS_ID]  # можно надевать на игрока

ITEMS_CAN_HAVE_MODS = [TYPE_WEAPONS_ID, TYPE_ARMOR_ID, TYPE_HELMETS_ID]  # можно вешать моды

# для определения куда можно вешать моды
ITEM_ASSOCIATIONS = {TYPE_WEAPONS_ID: TYPE_UPGRADES_WEAPON_ID, TYPE_ARMOR_ID: TYPE_UPGRADES_ARMOR_ID,
                     TYPE_HELMETS_ID: TYPE_UPGRADES_HELMET_ID}

# типы являющиеся улучшениями
UPGRADE_TYPES = [TYPE_UPGRADES_WEAPON_ID, TYPE_UPGRADES_ARMOR_ID, TYPE_UPGRADES_HELMET_ID]

ALL_TYPE_NAMES = ['items_param', TYPE_WEAPONS_NAME, TYPE_ARMOR_NAME,
                  TYPE_ARTEFACTS_NAME, TYPE_HELMETS_NAME,
                  TYPE_LOOT_CASES_NAME, TYPE_UPGRADES_WEAPON_NAME, TYPE_UPGRADES_ARMOR_NAME, TYPE_UPGRADES_HELMET_NAME, TYPE_USE_ITEMS_NAME]
ALL_TYPE_EMOJI = ['ERROR', '🔫', '👔', '🔮', '👒', '🎁', '⚙', '⚙', '⚙', '➕']
ITEMS_IN_ONE_PAGE = 8  # для отрисовки инвентаря

BONUS_INTO_ID = 32  # смещение для стакающихся предметов в скл инвентаре игрока

ARENA_REWARD = 50  # награда в монетах за победу на арене

BOSS_FIGHT_PRICE = 25  # расход энергии
ARENA_FIGHT_PRICE = 10  # расход энергии

ONE_MINUTE = 60
WAIT_EMPTY_DATA = 5

# Параметры игровых боссов
BOSS_ID = [0, 'user_id']
BOSS_USERNAME = [1, 'user_name']
BOSS_DAMAGE_TYPE = [2, 'damage_type']
BOSS_DAMAGE = [3, 'damage']
BOSS_CRIT_CHANCE = [4, 'crit_chance']
BOSS_CHANCE_TO_HIT = [5, 'chance_to_hit']
BOSS_ARMOR_RESIST = [6, 'armor']
BOSS_EMP = [7, 'emp']
BOSS_PUNCH = [8, 'punch']
BOSS_RAZRIV = [9, 'razriv']
BOSS_RADIATION = [10, 'radiation']
BOSS_BURN = [11, 'chemical_burn']
BOSS_BLAST = [12, 'blast']
BOSS_SHOT = [13, 'shot']
BOSS_REGEN = [14, 'regen']
BOSS_MAX_HP = [15, 'max_hp']
BOSS_DODGE = [16, 'dodge']
BOSS_PENETRATE = [17, 'penetrate']
BOSS_SOURCE = [18, 'source']
BOSS_FILENAME = [19, 'filename']
ALL_BOSS_PARAMS = [BOSS_ID, BOSS_USERNAME, BOSS_DAMAGE_TYPE, BOSS_DAMAGE, BOSS_CRIT_CHANCE, BOSS_CHANCE_TO_HIT,
                   BOSS_ARMOR_RESIST, BOSS_EMP, BOSS_PUNCH, BOSS_RAZRIV, BOSS_RADIATION,
                   BOSS_BURN, BOSS_BLAST, BOSS_SHOT, BOSS_REGEN, BOSS_MAX_HP, BOSS_DODGE, BOSS_PENETRATE, BOSS_SOURCE,
                   BOSS_FILENAME]


# Награда за боссов, хранится вне базы
MINI_BOSS_REWARD = 500

BOSS_SOBAKA_REWARD = [ARTEFACT_BLOODSTONE]
BOSS_KABAN_REWARD = [WEAPON_SIP200]
BOSS_BANDIT_REWARD = [ARMOR_BANDIT_JACKET, WEAPON_OHOTKA, REWARD_SKIN_BANDIT]
BOSS_KROVOSOS_REWARD = [(200, MINI_BOSS_REWARD), REWARD_CASE_HELMETS]
BOSS_BURER_REWARD = [(300, MINI_BOSS_REWARD), REWARD_CASE_ARTEFACTS]
BOSS_STRELOK_REWARD = [(400, MINI_BOSS_REWARD), REWARD_CASE_UPGRADES, WEAPON_SHTORM, ARTEFACT_FLAME, ARMOR_BULAT,
                       MOD_EKRAN_HELM, REWARD_BACKGROUND_FALLOUT]
BOSS_HIMERA_REWARD = [(200, MINI_BOSS_REWARD), HELMET_SFERAM12, WEAPON_FT200, REWARD_CASE_DEFAULT]
BOSS_GIANT_REWARD = [(300, MINI_BOSS_REWARD), MOD_EKRAN_ARM, MOD_EKRAN_HELM, REWARD_CASE_DEFAULT]
BOSS_MONOLIT_REWARD = [(400, MINI_BOSS_REWARD), ARMOR_BERILL, WEAPON_GAUSS, REWARD_CASE_DEFAULT, ARTEFACT_OAZIS]
BOSS_BLACKST_REWARD = [(500, MINI_BOSS_REWARD), ARMOR_EXOSKELET_DOLG, ARMOR_EXOSKELET_SVOBODA, REWARD_CASE_DEFAULT, ARTEFACT_KOMPAS]

ALL_BOSSES_REWARD = {1: BOSS_SOBAKA_REWARD, 2: BOSS_KABAN_REWARD, 6: BOSS_BANDIT_REWARD, 11: BOSS_KROVOSOS_REWARD,
                     16: BOSS_BURER_REWARD, 21: BOSS_STRELOK_REWARD, 500: [(1, MINI_BOSS_REWARD)], 12: BOSS_HIMERA_REWARD,
                     17: BOSS_GIANT_REWARD, 22: BOSS_MONOLIT_REWARD, 23: BOSS_BLACKST_REWARD}
MAX_BOSSES_IN_LOCATION = 5  # нужна для смещения при смене локации

# всё, что кучкуется
STACKABLE_TYPE = [TYPE_LOOT_CASES_ID, TYPE_UPGRADES_WEAPON_ID, TYPE_UPGRADES_ARMOR_ID, TYPE_UPGRADES_HELMET_ID, TYPE_USE_ITEMS]

# для расчетов инвентаря из скл
MAX_ITEMS = 200
# MAX_ITEMS_ST = len(STACKABLE_TYPE) * BONUS_INTO_ID
END_PLAYER_ITEMS = MAX_ITEMS + 1
START_PLAYER_ITEMS = 1

# смещение на начало стакающихся итемов
# START_PLAYER_ITEMS_ST = MAX_ITEMS + 1
# END_PLAYER_ITEMS_ST = MAX_ITEMS + MAX_ITEMS_ST + 1

# количество боссов для статистики убийств
BOSS_COUNT = 20

# время неактивных действий до удаления из массива активных игроков в секундах
TIME_TO_ERASE_PLAYER = 1200
MY_STALKER_TIMEOUT = 8

GAME_RANDOM = None  # обьект для гспч, хранится здесь для вызова из нескольких файлов, общий на всех игроков

DB_TABLE_NAMES = [TYPE_ARMOR_NAME, TYPE_WEAPONS_NAME, TYPE_ARTEFACTS_NAME, TYPE_HELMETS_NAME,
                  TYPE_UPGRADES_WEAPON_NAME,
                  TYPE_UPGRADES_ARMOR_NAME, TYPE_UPGRADES_HELMET_NAME,
                  "background", "bosses", "item_type", "locations", "loot_cases", "skins", TYPE_USE_ITEMS_NAME]

# player param
PLAYER_ID = [0, 'user_id']
PLAYER_USERNAME = [1, 'user_name']
PLAYER_BACKGROUND = [2, 'background']
PLAYER_PREMIUM = [3, 'premium']
PLAYER_LOCATION = [4, 'location']
PLAYER_BALANCE = [5, 'balance']
PLAYER_LVL = [6, 'lvl']
PLAYER_OPIT = [7, 'opit']
PLAYER_ENERGY = [8, 'energy']
PLAYER_RATING = [9, 'rating']
PLAYER_DAMAGE = [10, 'damage']
PLAYER_ARMOR_RESIST = [11, 'armor']
PLAYER_EMP = [12, 'emp']
PLAYER_PUNCH = [13, 'punch']
PLAYER_RAZRIV = [14, 'razriv']
PLAYER_RADIATION = [15, 'radiation']
PLAYER_BURN = [16, 'chemical_burn']
PLAYER_BLAST = [17, 'blast']
PLAYER_SHOT = [18, 'shot']
PLAYER_REGEN = [19, 'regen']
PLAYER_CURRENT_HP = [20, 'current_hp']
PLAYER_MAX_HP = [21, 'max_hp']
PLAYER_DOLLARS = [22, 'dollars']
PLAYER_LEFT_HAND = [23, 'left_hand']
PLAYER_RIGHT_HAND = [24, 'right_hand']
PLAYER_ARTEFACT = [25, 'active_artefact']
PLAYER_ARMOR_ITEM = [26, 'active_armor']
PLAYER_HELMET = [27, 'helmet']
PLAYER_CRIT_CHANCE = [28, 'crit_chance']
PLAYER_BAR_ID = [29, 'bar']
PLAYER_SKIN = [30, 'skin']
PLAYER_CHANCE_TO_HIT = [31, 'chance_to_hit']
PLAYER_DAMAGE_TYPE = [32, 'damage_type']
PLAYER_DODGE = [33, 'dodge']
PLAYER_ITEMS_RATING = [34, 'items_rating']
PLAYER_GROUP_ID = [35, 'group_id']
PLAYER_LAST_PEER_ID = [36, 'last_peer_id']
PLAYER_IS_BANED = [37, 'is_ban']
PLAYER_PENETRATE = [38, 'penetrate']
PLAYER_EVENTS = [39, 'events']
PLAYER_SKINS = [40, 'skins']
PLAYER_BACKGROUNDS = [41, 'backgrounds']
PLAYER_REF_SRC = [42, 'ref_src']
PLAYER_STALKER_IMAGE = [43, 'img']

ALL_PLAYER_PARAMS = [PLAYER_ID, PLAYER_USERNAME, PLAYER_BACKGROUND, PLAYER_PREMIUM, PLAYER_LOCATION, PLAYER_BALANCE,
                     PLAYER_LVL, PLAYER_OPIT, PLAYER_ENERGY, PLAYER_RATING, PLAYER_DAMAGE, PLAYER_ARMOR_RESIST,
                     PLAYER_EMP, PLAYER_PUNCH,
                     PLAYER_RAZRIV, PLAYER_RADIATION, PLAYER_BURN, PLAYER_BLAST, PLAYER_SHOT, PLAYER_REGEN,
                     PLAYER_CURRENT_HP, PLAYER_MAX_HP,
                     PLAYER_DOLLARS, PLAYER_LEFT_HAND, PLAYER_RIGHT_HAND, PLAYER_ARTEFACT, PLAYER_ARMOR_ITEM,
                     PLAYER_HELMET,
                     PLAYER_CRIT_CHANCE, PLAYER_BAR_ID, PLAYER_SKIN, PLAYER_CHANCE_TO_HIT, PLAYER_DAMAGE_TYPE,
                     PLAYER_DODGE, PLAYER_ITEMS_RATING,
                     PLAYER_GROUP_ID, PLAYER_LAST_PEER_ID, PLAYER_IS_BANED,
                     PLAYER_PENETRATE, PLAYER_EVENTS, PLAYER_SKINS, PLAYER_BACKGROUNDS, PLAYER_REF_SRC, PLAYER_STALKER_IMAGE]

ALL_PLAYER_PARAMS_NAMES = [ALL_PLAYER_PARAMS[i][1] for i in range(len(ALL_PLAYER_PARAMS))]

ITEMS_SKIN_ASSOCIATION = {TYPE_WEAPONS_ID: [PLAYER_LEFT_HAND, PLAYER_RIGHT_HAND], TYPE_ARMOR_ID: PLAYER_ARMOR_ITEM,
                          TYPE_ARTEFACTS_ID: PLAYER_ARTEFACT, TYPE_HELMETS_ID: PLAYER_HELMET}

PLAYER_RESISTS_DIVISOR = 5  # учитывается в формулах расчета многих базовых параметров игрока
PLAYER_MAX_RESIST = 90  # процент резистов
COMBAT_TYPE_ARENA = 1
COMBAT_TYPE_BOSS = 2

COMBAT_LEFT_SIDE = 1
COMBAT_RIGHT_SIDE = 2
COMBAT_LAST_TURN = 30

WEAPONS_BUST_PARAMS_NAME = [PLAYER_DAMAGE[1], PLAYER_CRIT_CHANCE[1], PLAYER_CHANCE_TO_HIT[1], PLAYER_PENETRATE[1]]
ARMORS_BUST_PARAMS_NAME = [PLAYER_ARMOR_RESIST[1], PLAYER_EMP[1], PLAYER_PUNCH[1], PLAYER_RAZRIV[1],
                           PLAYER_RADIATION[1],
                           PLAYER_BURN[1], PLAYER_BLAST[1], PLAYER_SHOT[1], PLAYER_REGEN[1], PLAYER_MAX_HP[1],
                           PLAYER_DODGE[1]]

DAMAGE_TYPES = ['Норма', 'Удар', 'Разрыв', 'Хим. Ожог', 'Взрыв', 'Радиация', 'Электро']
DAMAGE_TYPES_DB_NAME = [PLAYER_SHOT[1], PLAYER_PUNCH[1], PLAYER_RAZRIV[1], PLAYER_BLAST[1], PLAYER_BURN[1],
                        PLAYER_RADIATION[1], PLAYER_EMP[1]]
DAMAGE_TYPES_EMOJI = ['🔫', '👊', '💢', '☣', '💥', '☢', '⚡']

# temp_data_types:
LOTS_ID_FROM_AUCTION = 1
SELECTED_LOT_FROM_AUCTION = 2
SOME_ITEMS_FROM_AUCTION = 3
TEMP_BACKGROUND_ID_INDEX = 4
TEMP_MINI_GAME2_INDEX = 5
TEMP_MINI_GAME3_INDEX = 6

# ошибки
ERROR = -1
NO_STACK_ERROR = -2
SLOT_IS_BUSY_ERROR = -3
NO_HAVE_MODS_ERROR = -4
NEED_MORE_DATA_ERROR = -5
NOT_ENOUGH_ITEMS_ERROR = -6
ITEM_NOT_FOUND_ERROR = -7
NEED_MORE_MONEY_ERROR = -8
PLAYER_NOT_FOUND_ERROR = -9
PLAYER_NOT_HAVE_GROUP_ERROR = -10
MESSAGE_SEND_ERROR = -11
TIMEOUT_ERROR = -12
SUCCESSFUL = 1
ITEM_WAS_REMOVED = 2
GROUP_WAS_REMOVED = 3
GROUP_WAS_RESTORED = 4

# locations
LOCATION_KORDON = 1
LOCATION_SVALKA = 2
LOCATION_YANTAR = 3
LOCATION_X16 = 4
LOCATION_PRIPYAT = 5

# answers keyboard
KEYBOARD_MAIN = 1
BASE_KEYBOARD_DATA = open("keyboards/main.json", "r", encoding="UTF-8").read()
CAROUSEL_KEYBOARD = open("keyboards/carousel.json", "r", encoding="UTF-8").read()

# Навыки игрока описания
SKILL_GRENADE_THROW = ['💣 Бросок гранаты',
                       '💥 Сталкер бросает гранату, оглушая противника.🛡 Защита противника будет снижена на три хода. Перезарядка 1 ход ⌛']
SKILL_HEAD_SHOT = ['💢 Выстрел в голову',
                   '🔫 Сталкер делает выстрел в голову противника, нанося критический урон. Перезарядка 2 хода ⌛']
SKILL_TANK = ['🏚 Найти укрытие',
              '♻ Сталкер занимает более удобную позицию.🛡 Его защита возрастает на три хода. Перезарядка 1 ход ⌛']
ALL_SKILLS = {1: SKILL_GRENADE_THROW, 2: SKILL_HEAD_SHOT, 3: SKILL_TANK}
ALL_SKILLS_EMOJI = ['err', '💣', '💢', '🏚']

# events формат: [тип, таргет, количество ходов, чо-нибудь]
EVENT_BOMB = 1
EVENT_HEAD_SHOT = 2
EVENT_TANK = 3

KEYBOARD_NONE = [1]
KEYBOARD_LOCATIONS = [2, '👶 Кордон', '🚮 Свалка', '💉 Янтарь', '⛔ Лаборатория X16', '💀 Припять']  # +

# Мини игры
KEYBOARD_MINI_GAME = [3, '🕹 Монетка', '🌲 Исследователь', '🎲 Напёрстки']

KEYBOARD_MINI_GAME1 = [15, '💰 Сделать ставку']
KEYBOARD_MINI_GAME1_1 = [18, '50', '100', '500', '1000', '5000']
KEYBOARD_MINI_GAME1_2 = [19, '♻ Повторить ставку', '🆕 Новая ставка']


KEYBOARD_MINI_GAME2 = [16, '2', '3', '4', '5']
KEYBOARD_MINI_GAME2_1 = [20, '50', '100', '500', '1000', '5000']
KEYBOARD_MINI_GAME2_2 = [21, 'nop']

KEYBOARD_MINI_GAME3 = [17, '💰 Сделать ставку']
KEYBOARD_MINI_GAME3_1 = [22, '50', '100', '500', '1000', '5000']
KEYBOARD_MINI_GAME3_2 = [23, 'Лево', 'Центр', 'Право']
# -----------------------------------------------------------------------------------

# Мой сталкер
MY_STALKER_QUEUE = Queue()  # формат [owner, msg, target, keyboard]
KEYBOARD_MY_STALKER = [4, '🌄 Выбрать фон', '🎭 Скины', '✏ Ник', '👖 Снять экипировку', '🔮 Навыки', '🏆 Топ Сталкеров',
                       '🆘 Помощь', '⚛ Все параметры']
KEYBOARD_CHANGE_NICKNAME = [24, 'error']
KEYBOARD_REMOVE_CLOTHES = [44, '🔫 Снять оружие', '👔 Снять бронежилет', '👒 Снять шлем', '🔮 Снять артефакт', '♻ Снять всё']
KEYBOARD_SHOW_RATING_CRIT = [53, '1&#8419;', '2&#8419;', '3&#8419;', '4&#8419;', '5&#8419;', '6&#8419;', '7&#8419;',
                      '8&#8419;', '🏅', '🗿']
KEYBOARD_VERIFICATION = [55, '✅ Да', '❌ Нет']
# -----------------------------------------------------------------------------------

# Охота
KEYBOARD_HUNTING = [5, '🔫 Атаковать']

MINI_BOSSES_SOURCE_LIST = ['photo-210036099_457240242',
                           'photo-210036099_457240243',
                           'photo-210036099_457240244',
                           'photo-210036099_457240245',
                           'photo-210036099_457240246',
                           'photo-210036099_457240247',
                           'photo-210036099_457240248',
                           'photo-210036099_457240249',
                           'photo-210036099_457240250',
                           'photo-210036099_457240251',
                           'photo-210036099_457240252',
                           'photo-210036099_457240253',
                           'photo-210036099_457240254',
                           'photo-210036099_457240255',
                           'photo-210036099_457240256',
                           'photo-210036099_457240257',
                           'photo-210036099_457240258',
                           'photo-210036099_457240259',
                           'photo-210036099_457240260'
                           ]
FIRST_HUNTING_GEN = True
HUNTING_TIME = 0
MINI_BOSS_OBJECT = None
# -----------------------------------------------------------------------------------

# Аукцион
KEYBOARD_AUCTION = [6, '💼 Мои лоты', '🔥 Посмотреть товары', '🔍 Поиск по названию', '💰 Перевод', '♻ Вернуть все лоты']
KEYBOARD_AUCTION_CONTINUE = [28, 'error']
KEYBOARD_AUCTION_SELECT_LOT = [29, 'error']
KEYBOARD_AUCTION_SELECT_LOT_2 = [30, '↩ Забрать с аукциона']
KEYBOARD_AUCTION_CHOOSE_LOT = [31, 'error']
KEYBOARD_AUCTION_WAIT_NAME = [32, 'error']
KEYBOARD_AUCTION_WAIT_SUM = [33, 'error']
# -----------------------------------------------------------------------------------

# Инвентарь
KEYBOARD_INVENTORY = [7, '⬅', '1&#8419;', '2&#8419;', '3&#8419;', '4&#8419;', '5&#8419;', '6&#8419;', '7&#8419;',
                      '8&#8419;', '➡']
KEYBOARD_SET_SELECTED_ITEM = [25, '♻ Надеть', '⚙ Добавить мод', '💰 Продать', '⚖ На аукцион', '🎁 Открыть', '🛠 Ремонт', '👋 Использовать']
KEYBOARD_ADD_MODE_TO_ITEM = [26, 'error']
KEYBOARD_COUNT_OF_SELL_ITEMS = [27, '1', '2', '5']
KEYBOARD_REMONT = [55, '✅ Чинить', '❌ Отмена']
# -----------------------------------------------------------------------------------

# Акции
KEYBOARD_SALES = [8, '🔎 Поиск клиентов для Сидоровича', '🤝 Модификация за аватарку']
SIDOROVICH_BONUS = 5000
# -----------------------------------------------------------------------------------

# Боссы
KEYBOARD_BOSSES = [9, '🐶 Одиночные', '🐲 Групповые', '👮 Моя группа']  # не используется
KEYBOARD_BOSS_SELECT = [34, 'error']
KEYBOARD_BOSS_FIGHT_PREPARATION = [35, '👮 Моя группа', '🔫 Атаковать']
KEYBOARD_BOSS_GROUP_TRUE = [36, '👥 Пригласить в группу', '🚫 Выйти из группы']
KEYBOARD_BOSS_GROUP_FALSE = [37, '👥 Пригласить в группу', '♻ Автопоиск группы']
KEYBOARD_GROUP_WAIT_USER_SOURCE = [38, 'error']
KEYBOARD_GROUP_WAIT_FOLLOW_ANSWER = [39, '✅ Принять', '❌ Отказаться']
KEYBOARD_GROUP_WAIT_BOSS_FIGHT = [40, '✅ Да', '❌ Нет']
KEYBOARD_FIGHT_MAGIC = [50, 'err']  # способности игроков
# -----------------------------------------------------------------------------------

# Арена
KEYBOARD_ARENA = [10, '⚔ Пойти на арену', '🏆 Топ Арены', '👊 Пойти с другом']
KEYBOARD_ARENA_WAIT_USER_SOURCE = [41, 'error']
KEYBOARD_ARENA_WAIT_FOLLOW_ANSWER = [42, '✅ Принять', '❌ Отказаться']
# -----------------------------------------------------------------------------------

# Лут кейсы
KEYBOARD_LOOT = [11, '🎒 Открыть кейс с хабаром', f'💰 Купить кейс {LOOT_CASE_DEFAULT[1]}', '📦 Все кейсы']
KEYBOARD_LOOT_ALL = [43, '🎒 Кейс с хабаром', '👒 Кейс со шлемами', '🔮 Кейс с артефактами', '⚙ Кейс модификаций']
# -----------------------------------------------------------------------------------

# Прочее
KEYBOARD_OTHER = [12, '💥 Случайный анекдот', '🌄 Получить стикеры']
# -----------------------------------------------------------------------------------

# Ссылки
KEYBOARD_SOURCE = [13, '✉ Беседа для активных сталкеров', '📈 Торговля между игроками']
# -----------------------------------------------------------------------------------

# Донат
KEYBOARD_DONUT = [14, '⚡ Энергетик', '💵 Скин наёмника', '🐻 Фон Freddy', '💪 Премиум']  # '🏧 Обменник', '🏪 Магазин', '📁 Наборы', '🔫 Уникальные предметы']
KEYBOARD_BUY_ANSWER = [56, '✅ Купить', '❌ Отмена']

SHOP_ENERGETIK = [1, TYPE_USE_ITEMS, 10000, 'photo-210036099_457241179']  # id, pid, price
SHOP_NAEMNIK = [2, TYPE_REWARDS_SKIN, 10050, 'photo-210036099_457240300']
SHOP_FREDDY = [2, TYPE_REWARDS_BACKGROUND, 10100, 'photo-210036099_457240179']

LAST_DONUT_ID = 0
DONUT_PREMIUM = [1, 50]
DONUT_TEST = [2, 10]
DONUT_ALL = [DONUT_PREMIUM, DONUT_TEST]
# -----------------------------------------------------------------------------------

# Фоны
KEYBOARD_BACKGROUNDS = [45, '🏠 Стандартный']
KEYBOARD_BACKGROUNDS_CHOSE = [46, '✅ Выбрать', '♻ Вернуться']
# -----------------------------------------------------------------------------------

# Скины
# STALKER_SKINS = {0: 'STALKER_DEFAULT_SKIN', 32: 'STALKER_SKIN_ADMIN', 1: 'STALKER_SKIN_BANDIT', 2: 'STALKER_SKIN_NAEMNIK', 3: 'STALKER_SKIN_VOENNIY'}
NO_ITEM_SKINS = [31]
ONLY_WEAPON_SKINS = [1, 2, 3, 4]

# KEYBOARD_SKINS = [47, '🔫 Бандит', '💵 Наёмник', '👮 Военный', '😎 Стандартный']
KEYBOARD_SKINS = [47, '😎 Стандартный']
KEYBOARD_SKINS_SELECT = [51, '✅ Выбрать', '♻ Вернуться']
# -----------------------------------------------------------------------------------

# Эвенты (не больше 31)
GAME_EVENT_TEST = 1
GAME_EVENT_TEST2 = 2
GAME_EVENT_VIPE = 3
GAME_EVENT_CLEAR_SKY = 4

KEYBOARD_EVENT1 = [48, '🎁 Получить']
KEYBOARD_EVENT2 = [49, '🎁 Получить']
KEYBOARD_EVENT3 = [50, '🎁 Скин', '🎁 Фон']
KEYBOARD_EVENT_VIPE = [52, '🎁 Получить']
KEYBOARD_EVENT_CLEAR_SKY = [54, '🎁 Получить']
# -----------------------------------------------------------------------------------

KEYBOARD_LAST_ID = 56  # Когда создаёшь новую клавиатуру добавляй +1 -- нужна просто чтобы не сбиться со счёта

# Номера двоичных массивов флагов для функций
BIN_TYPE_EVENTS = 1
BIN_TYPE_SKINS = 2
BIN_TYPE_BACKGROUNDS = 3
# -----------------------------------------------------------------------------------

KEYBOARD_INVENTORY_ANSWERS = ['⬅', '1⃣', '2⃣', '3⃣', '4⃣',
                              '5⃣', '6⃣', '7⃣', '8⃣', '➡']

EMOJI_NUMBER_ASSOTIATIONS = {'1⃣': 1, '2⃣': 2, '3⃣': 3, '4⃣': 4, '5⃣': 5, '6⃣': 6, '7⃣': 7, '8⃣': 8}

ANSWER_IF_NOT_READY = '🛠 Ещё в разработке'
DEFAULT_BOT_ANSWER = "🤔 Ну-ка повтори"
DEFAULT_BOT_EVENT_ANSWER = "❌ Ты уже участвовал в этой акции"
DEFAULT_IMAGE_PATH = 'textures/'
ARMORS_IMAGE_PATH = 'armors/'
BACKGROUND_IMAGE_PATH = 'backgrounds/'
HELMETS_IMAGE_PATH = 'helmets/'
SKINS_IMAGE_PATH = 'skins/'
WEAPONS_IMAGE_PATH = 'weapons/'
ARTEFACTS_IMAGE_PATH = 'artefacts/'
DEFAULT_IMAGE_FORMAT = '.png'
ITEM_INVENTORY_NAME_ADDICTION = '_INV'


DEFAULT_PARAM_TABLE = 'default/STALKER_TABLE'
DEFAULT_PICTURE_SOURCE = 'default/DEFAULT_PICTURE'
DEFAULT_PICTURE_VK = 'photo-210036099_457239234'
SIDOROVICH_PICTURE = 'photo-210036099_457239246'
ARENA_WIN_PICTURE = 'photo-210036099_457239272'
MONETKA_PICTURE = 'photo-210036099_457239284'
NAPERSTKI_PICTURE = 'photo-210036099_457240285'
BAR_PICTURE = 'photo-210036099_457239287'
ARENA_PICTURE = 'photo-210036099_457239288'
# VK_STICKER_SOURCE = 'https://vk.cc/ceHghk'

ADMINISTRATORS = [216523446]
# ADMINISTRATORS = []

# флаги сообщений если не подходит стандартные
MESSAGE_FLAG_NO_LINE = 1

CURRENT_PEER_ID = 0  # техническая переменная, используется как флаг и место назначения текущего сообщения


DEFAULT_NAME_ITEM_NAMES = 'name'
DEFAULT_NAME_FILENAME_LINE = 'filename'

ITEMS_PARAM_UID = 0
ITEMS_PARAM_PROTO_ID = 1
ITEMS_PARAM_TYPE = 2
ITEMS_PARAM_IZNOS = 3
ITEMS_PARAM_MODS = 4
ITEMS_PARAM_FLAGS = 5
ITEMS_PARAM_COUNT = 6
ITEMS_PARAM_OWNER = 7
ITEMS_PARAM_ALL = [ITEMS_PARAM_UID, ITEMS_PARAM_PROTO_ID, ITEMS_PARAM_TYPE, ITEMS_PARAM_IZNOS,
                   ITEMS_PARAM_MODS, ITEMS_PARAM_FLAGS, ITEMS_PARAM_COUNT, ITEMS_PARAM_OWNER]  # для парсинга

# для расчёта позиции модов на предметы
# MAX_MODS_COUNT = 10
# ITEMS_PARAM_COUNT = MAX_MODS_COUNT + len(ITEMS_PARAM_ALL)
# START_PARAM_MODS = ITEMS_PARAM_COUNT - MAX_MODS_COUNT
# END_PARAM_MODS = START_PARAM_MODS + MAX_MODS_COUNT - 1
ITEMS_PARAM_FULL = [i for i in range(ITEMS_PARAM_UID, ITEMS_PARAM_COUNT+1)]

# хардкодед, последние три переменные в половине скл баз должны подходить под эти адреса
FILENAME_NUMBER = -1
SOURCE_NUMBER = -2
PRICE_NUMBER = -3
START_CHANGED_PARAMETERS = 2
COUNT_NO_CHANGED_ITEM_PARAMS = START_CHANGED_PARAMETERS + (-1 * PRICE_NUMBER)

# шрифт для картинок
DEFAULT_FONT_FULL_PATH = 'fonts/textures/times.ttf'

DEFAULT_ANEKDOTS_PATH = 'bigText/anekdoti.txt'


# ///////////////////////////////////// дефайны для рефакторинга итемов
PRAGMA_WEAPONS = []
PRAGMA_ARMORS = []
PRAGMA_ARTEFACTS = []
PRAGMA_HELMETS = []
PRAGMA_LOOT_CASES = []
PRAGMA_UPGRADES_ARMOR = []
PRAGMA_UPGRADES_HELMET = []
PRAGMA_UPGRADES_WEAPON = []
PRAGMA_USE_ITEMS = []
PRAGMA_ITEMS_PARAM = []
PRAGMA_ALL = [PRAGMA_ITEMS_PARAM, PRAGMA_WEAPONS, PRAGMA_ARMORS, PRAGMA_ARTEFACTS, PRAGMA_HELMETS, PRAGMA_LOOT_CASES,
              PRAGMA_UPGRADES_WEAPON, PRAGMA_UPGRADES_ARMOR, PRAGMA_UPGRADES_HELMET, PRAGMA_USE_ITEMS]

# ////////////////////////////////////Флаги
ITEMS_FLAG_DAILY_BONUS = 1  # для упрощённого поиска по списку итемов
# ////////////////////////////////////////////////////////////////////////////////////////////////////////


def get_player(play_id):
    for i in range(len(player_objects)):
        if player_objects[i].user_id == play_id:
            return player_objects[i]
    return None


def restart_connection():
    global BH
    global GIVE
    global LONGPOLL
    BH = vk_api.VkApi(token=TOKEN, api_version=gc.ApiVersion)
    GIVE = BH.get_api()
    LONGPOLL = VkBotLongPoll(vk=BH, group_id=int(GROUP_BOT_ID))


def quicksort(nums):
   if len(nums) <= 1:
       return nums
   else:
       q = choice(nums)[1]
       s_nums = []
       m_nums = []
       e_nums = []
       for n in nums:
           if n[1] < q:
               s_nums.append(n)
           elif n[1] > q:
               m_nums.append(n)
           else:
               e_nums.append(n)
       return quicksort(s_nums) + e_nums + quicksort(m_nums)