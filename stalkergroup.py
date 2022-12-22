import defines as d

"""Класс, отвечающий за группы игроков, которые используются в походах на боссов"""


class Group:
    def __init__(self, players, group_id, connect=None, cursor=None):
        if not cursor:
            cursor = connect.cursor()
        try:
            cursor.execute(f'SELECT * from groups WHERE group_id = {group_id}')
            data = cursor.fetchall()[0]
        except IndexError:
            data = None
        self.group_id = group_id
        self.player1 = None
        self.player2 = None
        self.player3 = None
        self.count = 0  # количество игроков в команде
        if not data:
            if not players:
                self.group_id = 0
                return
            for player in players:
                if player.group_id:
                    self.group_id = 0
                    return
            cursor.execute(f'INSERT INTO groups (group_id) VALUES ({group_id})')
            connect.commit()
            self.add_obj_to_group(players, cursor)
            # connect.commit()
        else:
            for i in range(1, 4):
                if data[i]:
                    setattr(self, f'player{self.count + 1}', data[i])
                    self.count += 1
            if self.count <= 0:
                self.destroy_group(cursor)
                self.group_id = 0
            # if players[0] not in self.get_list_id():
            #     self.errors = d.ERROR

    def add_obj_to_group(self, players, cursor):
        lst = []
        for player in players:
            lst.append(player.user_id)
        if not self.__add_to_group(lst, cursor):
            for player in players:
                player.update_database_value(cursor, d.PLAYER_GROUP_ID, self.group_id)

    def __add_to_group(self, players, cursor):
        if self.count+len(players) > 3:
            return d.ERROR
        for player in players:
            for char in self.get_list_id():
                if char == player:
                    players.remove(player)
        for i in range(len(players)):
            cursor.execute(f'UPDATE groups set player{self.count + 1}={players[i]} WHERE group_id = {self.group_id}')
            setattr(self, f'player{self.count + 1}', players[i])
            # players[i].update_database_value(cursor, d.PLAYER_GROUP_ID, self.group_id)
            self.count += 1
        if self.count <= 0:
            self.destroy_group(cursor)
            return d.GROUP_WAS_REMOVED

    def remove_with_group(self, player, cursor):
        try:
            if player.group_id in d.wait_boss_fight:
                try:
                    d.wait_boss_fight.pop(player.group_id)
                except KeyError:
                    pass
            index = self.get_list_id().index(player.user_id) + 1
            cursor.execute(f'UPDATE groups set player{index}=0 WHERE group_id = {self.group_id}')
            self.count -= 1
            player.update_database_value(cursor, d.PLAYER_GROUP_ID, 0)
            setattr(self, f'player{index}', None)
            if self.count <= 0:
                self.destroy_group(cursor)
                return d.GROUP_WAS_REMOVED
            elif index < 3:
                self.restore_group(cursor)
                return d.GROUP_WAS_RESTORED
            return d.SUCCESSFUL
        except ValueError:
            return d.ERROR
        except IndexError:
            return d.ERROR

    def check_me(self, player):
        if player.user_id in self.get_list_id():
            return True

    # def is_valid(self):
    #     if self.group_id != 0:
    #         return True

    def get_list_id(self):
        lst = []
        if self.player1:
            lst.append(self.player1)
        if self.player2:
            lst.append(self.player2)
        if self.player3:
            lst.append(self.player3)
        return lst

    def restore_group(self, cursor):
        cursor.execute(f'UPDATE groups set player1 = 0, player2 = 0, player3 = 0 WHERE group_id = {self.group_id}')
        self.count = 0
        players = [self.player1, self.player2, self.player3]
        players = [x for x in players if x]
        self.player1 = None
        self.player2 = None
        self.player3 = None
        self.__add_to_group(players, cursor)

    def destroy_group(self, cursor):
        cursor.execute(f'DELETE FROM groups WHERE group_id = {self.group_id}')


def start():
    import sqlite3
    connect = sqlite3.connect('BotStalker.db', check_same_thread=False)
    cursor = connect.cursor()
    class Player:
        def __init__(self, _id):
            self.user_id = _id
    player1 = Player(15)
    player2 = Player(16)
    player3 = Player(17)
    test = Group([player1, player2, player3], 22, connect)
    # test.remove_with_group(player1, cursor)
    connect.commit()


if __name__ == '__main__':
    start()
