from random import randint
import socket
import sys


def send_data_to_player(playerr, data):
    playerr.connection.sendall(bytearray(data, 'ascii'))


def send_data_to_all_players(players, data):
    for gamer in players:
        send_data_to_player(gamer, data)


def bind_address(address, sock):
    try:
        sock.bind(address)
    except:
        print("Can`t bind address", file=sys.stderr)
        exit()
    else:
        print("Server is binded to address %s on port %s" % address, file=sys.stdout)

#zamienic box na deck

class IndexOut(Exception):
    pass


class Menu:

    names = ["Aces", "Twos", "Threes", "Fours", "Fives", "Sixes", "Three Of A Kind", "Four Of A Kind",
             "Full House", "Small Straight", "Large Straight", "Yahtzee", "Chance"]

    def print_menu(self):
        return "\n################################### MENU #############################\n" \
               "\n1. See your score\n" \
               "2. Re-roll a dice\n"  \
               "3. Bind points\n"   \
               "4. See your deck\n"  \
               "5. See menu again\n"

    def choose_action(self, player, gmaster, bmaster, cmaster):
        re_roll_counter = 2
        while 1:
            err_flag = False
            self.print_menu()
            while not err_flag:
                try:
                    choice = int(input("What do you want to do " + player.name + ": "))
                    if choice < 1 or choice > 5:
                        raise IndexOut
                except (ValueError, IndexOut):
                    print("\nWrong choice, type correct number!\n")
                else:
                    err_flag = True
            if choice == 1:
                player.show_score(self.names)
            elif choice == 2:
                if re_roll_counter != 0:
                    player.change_re_roll(gmaster.re_roll(player.box_of_dice))
                    re_roll_counter -= 1
                else:
                    print("\nYou can not re-roll more in this turn!\n")
            elif choice == 3:
                print("\n################################### BIND MENU ###################################")
                bmaster.bind_points(cmaster.check_all(player.allow_to_bind, player.box_of_dice),
                                    player.score_table, player.allow_to_bind)
                break
            elif choice == 4:
                print("Your deck:  " + str(player.box_of_dice) + "\n")
            elif choice == 5:
                print("\n\n")


class Dice:

    def roll_a_dice(self):
        return randint(1, 6)

    def start_roll(self):
        numbers = [0, 0, 0, 0, 0]
        for throw in range(5):
            numbers[throw] = self.roll_a_dice()
        return numbers

    def re_roll(self, numbers):
        err_flag = False
        while not err_flag:
            try:
                no_boxes = input("\nType numbers of boxes that you want reroll (1-5 with space, or enter for no reroll): ").split(" ")
                if no_boxes[0] == '':
                    return numbers
                else:
                    for index in no_boxes:
                        numbers[int(index)-1] = self.roll_a_dice()
                    print("\nNow you have: ", numbers)
                    return numbers
            except (IndexError, ValueError):
                print("\nType numbers of dices correctly! Use only digits 1-5 separated with space!\n")
            else:
                err_flag = True
        # if empty return the same values, if not empty, change values.

    def check_winner(self, player1, player2):
        if player1.allow_to_bind.count(False) == 13:
            if sum(player1.score_table) > sum(player2.score_table):
                print("Player 1 - ", player1.name, " Wins! He has ", sum(player1.score_table), " points")
                print("Player 2 - ", player2.name, "has ", sum(player2.score_table), " points")
                return 1
            elif sum(player2.score_table) > sum(player1.score_table):
                print("Player 2 - ", player2.name, " Wins! He has ", sum(player2.score_table), " points")
                print("Player 1 - ", player1.name, "has ", sum(player1.score_table), " points")
                return 1
            else:
                print("DRAW! Points: ", sum(player1.score_table))
                return 1
        else:
            return 0


class Player:

    def __init__(self, start_roll, connection, address):
        self.connection = connection
        self.address = address[0] + ":" + str(address[1])
        self.box_of_dice = start_roll               # check class will could read from this, each dice
        self.score_table = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.allow_to_bind = [True, True, True, True,
                              True, True, True, True,
                              True, True, True, True, True]
        self.name = None

    def change_re_roll(self, new_values):
        self.box_of_dice = new_values               # change values from outside

    def show_score(self, names):
        print("\n ################################### YOUR SCORE! ###################################\n")
        for index, name in enumerate(names):
            print(name, ": ", self.score_table[index])

    def recv_name(self):
        while True:
            data = connection.recv(1024)
            if data:
                self.name = data.decode("ascii")
                response = bytearray("name_recived", 'ascii')
                connection.sendall(response)
                break


class Check:

    def check_upper(self, enable, player_box):

        # there will be boolean table from bind class which tell us what should be
        # displayed and calculated, if binded already, value remain the same as before.

        names = ["\n1. Aces", "2. Twos", "3. Threes", "4. Fours", "5. Fives", "6. Sixes"]
        calculation = lambda number: player_box.count(number) * number
        # check how many there are numbers 1-6 function

        for numbers in range(1, 7):    # each numbers 1-6
            if enable[numbers-1]:     # check if already binded
                print(names[numbers - 1], " - Points: ", calculation(numbers))
                names[numbers-1] = calculation(numbers)  # calculate and display

        return names
        # no matter what, return values, even if there was not any calculation
        # player won`t see this and won`t be able to bind older value because boolean table

    def check_count(self, player_box, count):
        for numbers in player_box:
            if player_box.count(numbers) == count:
                return True
            else:
                continue
        return False

    def check_three_kind(self, enable, player_box):
        if enable[6] and self.check_count(player_box, 3):
            print("7. Three Of A Kind - Points: ", sum(player_box))
            return [sum(player_box)]
        elif enable[6]:
            print("7. Three Of A Kind - Points: 0")
            return [0]
        else:
            return [999]
        # check if there is three same elements of set in box
        # must be three numbers in set

    def check_four_kind(self, enable, player_box):
        if enable[7] and self.check_count(player_box, 4):
            print("8. Four Of A Kind - Points: ", sum(player_box))
            return [sum(player_box)]
        elif enable[7]:
            print("8. Four Of A Kind - Points: 0")
            return [0]
        else:
            return [999]
        # check if there is four same elements of set in box

    def check_full_house(self, enable, player_box):
        sorted_box = sorted(player_box)
        if enable[8] and ((sorted_box[0:3].count(sorted_box[0]) == 3 and sorted_box[3:6].count(sorted_box[4]) == 2) or
                          (sorted_box[0:2].count(sorted_box[0]) == 2 and sorted_box[2:6].count(sorted_box[3]) == 3)):
            print("9. Full House - Points: 25")
            return [25]
        elif enable[8]:
            print("9. Full House - Points: 0")
            return [0]
        else:
            return [999]
        # If any of these two numbers appear in box 4 times it is impossible to find full house

    def straight_counter(self, enable, player_box):
        if enable[9] or enable[10]:                     # check if there is point of searching straight
            wanteds = sorted(list(set(player_box)))
            counter = 0
            for i, number in enumerate(wanteds):
                if i == 0:
                    counter += 1
                    continue
                elif number == wanteds[i - 1] + 1:
                    counter += 1
                elif counter != 4 and counter != 5:
                    counter = 0
            return counter

        # check if there is combination 1-2-3-4 , 1-2-3-4-5, 2-3-4-5

    def check_small_straight(self, enable, player_box):
        if self.straight_counter(enable, player_box) == 4 and enable[9]:
            print("10. Small Straight - Points: 30")
            return [30]
        elif enable[9]:
            print("10. Small Straight - Points: 0")
            return [0]
        else:
            return [999]

    def check_large_straight(self, enable, player_box):
        if self.straight_counter(enable, player_box) == 5:
            print("11. Large Straight - Points: 40")
            return [40]
        elif enable[10]:
            print("11. Large Straight - Points: 0")
            return [0]
        else:
            return [999]

    def check_yahtzee(self, enable, player_box):
        if player_box.count(player_box[0]) == 5 and enable[11]:
            print("12. Yahtzee - Points: 50")
            return [50]
        elif enable[11]:
            print("12. Yahtzee - Points: 0")
            return [0]
        else:
            return [999]

    def check_chance(self, enable, player_box):
        if enable[12]:
            print("13. Chance - Points: ", sum(player_box))
            return [sum(player_box)]
        else:
            return [999]

    def check_all(self, enable, player_box):
        return (self.check_upper(enable, player_box) +
                self.check_three_kind(enable, player_box) +
                self.check_four_kind(enable, player_box) +
                self.check_full_house(enable, player_box) +
                self.check_small_straight(enable, player_box) +
                self.check_large_straight(enable, player_box) +
                self.check_yahtzee(enable, player_box) +
                self.check_chance(enable, player_box))


class Bind:

    def bind_points(self, calculation_table, player_scores, permission):  # write and read reference!!!
        flag = True   # if choose correct index, change to False
        err_flag = False
        while flag:
            while not err_flag:
                try:
                    index = int(input("\nType index of points you want to bind to your score: "))
                    if index < 1 or index > 13:
                        raise IndexOut
                except (ValueError, IndexOut):
                    print("Type correct number (only one number 1-13)")
                else:
                    err_flag = True
            if permission[index-1]:
                flag = False    # let go out the loop
                player_scores[index-1] = calculation_table[index-1]  # write value by reference to table in object
                permission[index-1] = False   # Block binding this points again
            else:
                print("\nYou choose bad index. Try again!\n")


if __name__ == "__main__":
    game_manager = Dice()  # Initialization of Game manager
    check_manager = Check()  # Initialization of Check manager
    bind_manager = Bind()  # Initialization of Bind manager
    menu_manager = Menu()  # Initialization of Menu manager

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    local_address = ("localhost", 10000)
    bind_address(local_address, sock)
    sock.listen(1)
    connections = 2
    Players = []
    while connections:
        connection, player_address = sock.accept()
        if len(player_address) != 0:
            player = Player(game_manager.start_roll(), connection, player_address)
            player.recv_name()
            Players.append(player)

    for player in Players:
        send_data_to_all_players(Players, "GameStart")

    while 1:
        send_data_to_player(Players[0], "Start")
        send_data_to_player(Players[1], "FIN")
        send_data_to_all_players(Players, "Turn: " + str(Players[0].name))
        send_data_to_all_players(Players, menu_manager.print_menu() + "\nNow you have: " + str(Players[0].box_of_dice))


        menu_manager.choose_action(Player[0],
        player1.change_re_roll(game_manager.start_roll())

        print("----------------------------------------", player2.name.upper(), "----------------------------------------")
        print("Now you have:", player2.box_of_dice)
        menu_manager.choose_action(player2, game_manager, bind_manager, check_manager)
        player2.change_re_roll(game_manager.start_roll())

        if game_manager.check_winner(player1, player2):
            break