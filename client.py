import socket
import sys


def send_to_server(socket_server, data):
    socket_server.sendall(bytearray(data, 'ascii'))


def recv_from_server(socket_server):
    data_rcv = socket_server.recv(2048)
    return data_rcv.decode('ascii')


if __name__ == "__main__":

    name = input("Type your name: ")

    sock = None
    server_address = None

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except:
        print("Can`t create socket!  Program will be closed!", file=sys.stderr)
        exit()

    address = input("Type server name: ")

    try:
        address = socket.gethostbyname(address)
    except:
        print("Can`t resolve this name. Try insert ip address of server", file=sys.stdout)
        address = input("Server IP: ")

    server_address = (address, 10000)

    print("Connecting to server", file=sys.stdout)

    try:
        sock.connect(server_address)
    except:
        print("Can`t connect to the server! Program will be closed!", file=sys.stderr)
        exit()

    sock.sendall(bytearray(name, 'ascii'))

    response = 0

    while response != "name_recived":
        response = sock.recv(1024).decode('ascii')

    print("Wait for game start!", file=sys.stdout)

    signal = None

    while signal != "GameStart":
        signal = sock.recv(1024)
        signal = signal.decode('ascii')

    print("after Gamestart")

    input_enable = False

    while True:
        try:
            data = recv_from_server(sock)
            if "Input_enable" not in data:
                print(data)
            else:
                response = ""
                while response == "":
                        response = input("Input: ")
                send_to_server(sock, response)
            if "Closing!" in data:
                break
        except KeyboardInterrupt:
            response = "Disconnect"
            send_to_server(sock, response)
