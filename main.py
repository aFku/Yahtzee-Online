from random import randint
import socket
import sys
import time
import logging, logging.handlers
import sys, os, atexit
from signal import SIGTERM


class Daemon:
    """
    A generic daemon class.

    Usage: subclass the Daemon class and override the run() method
    """

    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile

    def daemonize(self):
        """
        do the UNIX double-fork magic, see Stevens' "Advanced
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except Exception as e:
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                sys.exit(0)
        except Exception as e:
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(self.stdin, 'r')
        so = open(self.stdout, 'a+')
        se = open(self.stderr, 'a+')
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # write pidfile
        atexit.register(self.delpid)
        pid = str(os.getpid())
        open(self.pidfile, 'w+').write("%s\n" % pid)

    def delpid(self):
        os.remove(self.pidfile)

    def start(self):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        try:
            pf = open(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if pid:
            message = "pidfile %s already exist. Daemon already running?\n"
            sys.stderr.write(message % self.pidfile)
            sys.exit(1)

        # Start the daemon
        self.daemonize()
        self.run()

    def stop(self):
        """
        Stop the daemon
        """
        # Get the pid from the pidfile
        try:
            pf = open(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if not pid:
            message = "pidfile %s does not exist. Daemon not running?\n"
            sys.stderr.write(message % self.pidfile)
            return  # not an error in a restart

        # Try killing the daemon process
        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except Exception as err :
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                sys.exit(1)

    def restart(self):
        """
        Restart the daemon
        """
        self.stop()
        self.start()

    def run(self):
        """
        You should override this method when you subclass Daemon. It will be called after the process has been
        daemonized by start() or restart().
        """


class PlayerDisconnect(Exception):
    pass


def recv_from_player(playerr):
    data = 0
    while not data:
        data = playerr.connection.recv(1024)
        data = data.decode('ascii')
        if data == "Disconnect":
            raise PlayerDisconnect
    return data


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
               "5. See menu again\n" \
               "6. See your opponent points\n"

    def choose_action(self, player, gmaster, bmaster, cmaster, opponent):
        choice = 0
        re_roll_counter = 2
        while 1:
            err_flag = False
            self.print_menu()
            while not err_flag:
                try:
                    send_data_to_player(player, self.print_menu())
                    time.sleep(0.1)
                    send_data_to_player(player, "Input_enable")
                    choice = int(recv_from_player(player))
                    if choice < 1 or choice > 6:
                        raise IndexOut
                except (ValueError, IndexOut):
                    send_data_to_player(player, "\nWrong choice, type correct number!\n")
                else:
                    err_flag = True
            if choice == 1:
                send_data_to_player(player, "\n ################################### YOUR SCORE! ###################################\n")
                time.sleep(0.05)
                send_data_to_player(player, player.show_score(self.names))
            elif choice == 2:
                if re_roll_counter != 0:
                    player.change_re_roll(gmaster.re_roll(player))
                    re_roll_counter -= 1
                else:
                    send_data_to_player(player, "\nYou can not re-roll more in this turn!\n")
            elif choice == 3:
                send_data_to_player(player ,"\n################################### BIND MENU ###################################")
                time.sleep(0.05)
                bmaster.bind_points(cmaster.check_all(player),
                                    player.score_table, player.allow_to_bind, player)
                break
            elif choice == 4:
                send_data_to_player(player, "Your deck:  " + str(player.box_of_dice) + "\n")
            elif choice == 5:
                send_data_to_player(player, "\n\n")
            elif choice == 6:
                send_data_to_player(player,
                                    "\n ################################### OPPONENTs SCORE! ###################################\n")
                time.sleep(0.05)
                send_data_to_player(player, opponent.show_score(self.names))


class Dice:

    def roll_a_dice(self):
        return randint(1, 6)

    def start_roll(self):
        numbers = [0, 0, 0, 0, 0]
        for throw in range(5):
            numbers[throw] = self.roll_a_dice()
        return numbers

    def re_roll(self, player):
        numbers = player.box_of_dice
        err_flag = False
        while not err_flag:
            try:
                send_data_to_player(player, "\nType numbers of boxes that you want reroll (1-5 with space, or enter for no reroll): ")
                send_data_to_player(player, "Input_enable")
                no_boxes = recv_from_player(player).split(" ")
                if no_boxes[0] == '':
                    return numbers
                else:
                    for index in no_boxes:
                        numbers[int(index)-1] = self.roll_a_dice()
                    send_data_to_player(player, "\nNow you have: " + str(numbers))
                    return numbers
            except (IndexError, ValueError):
                send_data_to_player(player, "\nType numbers of dices correctly! Use only digits 1-5 separated with space!\n")
        # if empty return the same values, if not empty, change values.

    def check_winner(self, players, logger):
        if players[0].allow_to_bind.count(False) == 13:
            if sum(players[0].score_table) > sum(players[1].score_table):
                send_data_to_all_players(players, "Player 1 - " + players[0].name + " Won! Winner has " + str(sum(players[0].score_table)) + " points")
                time.sleep(0.01)
                send_data_to_all_players(players, "Player 2 - " + players[1].name + " has " + str(sum(players[1].score_table)) + " points")
                logger.info(players[0].name + ' won with ' + str(sum(players[0].score_table)) + 'points! Second player ' +
                            players[1].name + ' has ' + str(sum(players[1].score_table)) + 'points')
                return 1
            elif sum(players[1].score_table) > sum(players[0].score_table):
                send_data_to_all_players(players, "Player 2 - " + players[1].name + " Wins! He has " + str(sum(players[1].score_table)) + " points")
                send_data_to_all_players(players, "Player 1 - " + players[0].name + " has " + str(sum(players[0].score_table)) + " points")
                logger.info(players[1].name + ' won with ' + str(sum(players[1].score_table)) + 'points! Second player ' +
                            players[0].name + ' has ' + str(sum(players[0].score_table)) + 'points')
                return 1
            else:
                send_data_to_all_players(players, "DRAW! Points: " + str(sum(players[0].score_table)))
                logger.info("DRAW! Points: " + str(sum(players[0].score_table)))
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
        score = ""
        for index, name in enumerate(names):
            score += name + ": " + str(self.score_table[index]) + "\n"
        return score


    def recv_name(self):
        while True:
            data = connection.recv(1024)
            if data:
                self.name = data.decode("ascii")
                response = bytearray("name_recived", 'ascii')
                connection.sendall(response)
                break


class Check:

    def check_upper(self, enable, player_box, player):

        # there will be boolean table from bind class which tell us what should be
        # displayed and calculated, if binded already, value remain the same as before.

        names = ["\n1. Aces", "2. Twos", "3. Threes", "4. Fours", "5. Fives", "6. Sixes"]
        calculation = lambda number: player_box.count(number) * number
        # check how many there are numbers 1-6 function

        for numbers in range(1, 7):    # each numbers 1-6
            if enable[numbers-1]:     # check if already binded
                send_data_to_player(player, names[numbers - 1] + " - Points: " + str(calculation(numbers)) + "\n")
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

    def check_three_kind(self, enable, player_box, player):
        if enable[6] and self.check_count(player_box, 3):
            send_data_to_player(player, "7. Three Of A Kind - Points: " + str(sum(player_box)) + "\n")
            return [sum(player_box)]
        elif enable[6]:
            send_data_to_player(player, "7. Three Of A Kind - Points: 0" + "\n")
            return [0]
        else:
            return [999]
        # check if there is three same elements of set in box
        # must be three numbers in set

    def check_four_kind(self, enable, player_box, player):
        if enable[7] and self.check_count(player_box, 4):
            send_data_to_player(player, "8. Four Of A Kind - Points: " + str(sum(player_box)) + "\n")
            return [sum(player_box)]
        elif enable[7]:
            send_data_to_player(player, "8. Four Of A Kind - Points: 0" + "\n")
            return [0]
        else:
            return [999]
        # check if there is four same elements of set in box

    def check_full_house(self, enable, player_box, player):
        sorted_box = sorted(player_box)
        if enable[8] and ((sorted_box[0:3].count(sorted_box[0]) == 3 and sorted_box[3:6].count(sorted_box[4]) == 2) or
                          (sorted_box[0:2].count(sorted_box[0]) == 2 and sorted_box[2:6].count(sorted_box[3]) == 3)):
            send_data_to_player(player, "9. Full House - Points: 25" + "\n")
            return [25]
        elif enable[8]:
            send_data_to_player(player, "9. Full House - Points: 0" + "\n")
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

    def check_small_straight(self, enable, player_box, player):
        if self.straight_counter(enable, player_box) == 4 and enable[9]:
            send_data_to_player(player, "10. Small Straight - Points: 30" + "\n")
            return [30]
        elif enable[9]:
            send_data_to_player(player, "10. Small Straight - Points: 0" + "\n")
            return [0]
        else:
            return [999]

    def check_large_straight(self, enable, player_box, player):
        if self.straight_counter(enable, player_box) == 5:
            send_data_to_player(player, "11. Large Straight - Points: 40" + "\n")
            return [40]
        elif enable[10]:
            send_data_to_player(player, "11. Large Straight - Points: 0" + "\n")
            return [0]
        else:
            return [999]

    def check_yahtzee(self, enable, player_box, player):
        if player_box.count(player_box[0]) == 5 and enable[11]:
            send_data_to_player(player, "12. Yahtzee - Points: 50" + "\n")
            return [50]
        elif enable[11]:
            send_data_to_player(player, "12. Yahtzee - Points: 0" + "\n")
            return [0]
        else:
            return [999]

    def check_chance(self, enable, player_box, player):
        if enable[12]:
            send_data_to_player(player, "13. Chance - Points: " + str(sum(player_box)) + "\n")
            time.sleep(0.05)
            return [sum(player_box)]
        else:
            return [999]

    def check_all(self, player):
        enable = player.allow_to_bind
        player_box = player.box_of_dice
        return (self.check_upper(enable, player_box, player) +
                self.check_three_kind(enable, player_box, player) +
                self.check_four_kind(enable, player_box, player) +
                self.check_full_house(enable, player_box, player) +
                self.check_small_straight(enable, player_box, player) +
                self.check_large_straight(enable, player_box, player) +
                self.check_yahtzee(enable, player_box, player) +
                self.check_chance(enable, player_box, player))


class Bind:

    def bind_points(self, calculation_table, player_scores, permission, player):  # write and read reference!!!
        flag = True   # if choose correct index, change to False
        while flag:
            err_flag = False
            while not err_flag:
                try:
                    time.sleep(0.05)
                    send_data_to_player(player,
                                        "\nType number to bind: ")
                    send_data_to_player(player, "Input_enable")
                    index = int(recv_from_player(player))
                    if index < 1 or index > 13:
                        raise IndexOut
                except (ValueError, IndexOut):
                    send_data_to_player(player, "Type correct number (only one number 1-13)")
                else:
                    err_flag = True
            if permission[index-1]:
                flag = False    # let go out the loop
                player_scores[index-1] = calculation_table[index-1]  # write value by reference to table in object
                permission[index-1] = False   # Block binding this points again
            else:
                send_data_to_player(player, "\nYou choose bad index. Try again!\n")


if __name__ == "__main__":
    daemon = Daemon('pid.pid')
    daemon.start()

    my_logger = logging.getLogger('MyLogger')
    my_logger.setLevel(logging.DEBUG)
    handler = logging.handlers.SysLogHandler(address= '/dev/log')
    my_logger.addHandler(handler)

    game_manager = Dice()  # Initialization of Game manager
    check_manager = Check()  # Initialization of Check manager
    bind_manager = Bind()  # Initialization of Bind manager
    menu_manager = Menu()  # Initialization of Menu manager

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    local_address = ("localhost", 10000)
    bind_address(local_address, sock)
    sock.listen(1)
    while 1:
        my_logger.info('Server start listening')
        connections = 2
        Players = []
        while connections:
            connection, player_address = sock.accept()
            if len(player_address) != 0:
                player = Player(game_manager.start_roll(), connection, player_address)
                player.recv_name()
                Players.append(player)
                connections -= 1
                my_logger.info('Player connected with IP: ' + str(player_address) + ' and with name: ' + player.name)

        my_logger.info('Game started')

        time.sleep(0.1)

        send_data_to_all_players(Players, "GameStart")

        time.sleep(0.1)

        while 1:
                try:
                    send_data_to_all_players(Players, "\nTurn: " + str(Players[0].name))
                    send_data_to_player(Players[1], "\nWait for your turn!\n\n")
                    time.sleep(0.1)
                    Players[0].change_re_roll(game_manager.start_roll())
                    send_data_to_player(Players[0], "\nNow you have: " + str(Players[0].box_of_dice))
                    menu_manager.choose_action(Players[0], game_manager, bind_manager, check_manager, Players[1])

                    send_data_to_all_players(Players, "\nTurn: " + str(Players[1].name))
                    send_data_to_player(Players[0], "\nWait for your turn!\n\n")
                    time.sleep(0.1)
                    Players[1].change_re_roll(game_manager.start_roll())
                    send_data_to_player(Players[1], "\nNow you have: " + str(Players[1].box_of_dice))
                    menu_manager.choose_action(Players[1], game_manager, bind_manager, check_manager, Players[0])

                    if game_manager.check_winner(Players, my_logger):
                        time.sleep(0.1)
                        send_data_to_all_players(Players, "Closing!")
                        break
                except PlayerDisconnect:
                    send_data_to_all_players(Players, "\nOne of the player disconnect from server!\nClosing!")
                    my_logger.error('Player has been disconnected from game before end! Session will be wiped!')


