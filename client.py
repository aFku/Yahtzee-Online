import socket
import sys


def send_to_server(socket_server, data):
    socket_server.sendall(bytearray(data, 'ascii'))


def recv_from_server(socket_server):
    data_rcv = socket_server.recv(2048)
    return data_rcv.decode('ascii')



name = input("Type your name: ")

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_address = ("localhost", 10000)

print("Connecting to server", file=sys.stdout)

sock.connect(server_address)

sock.sendall(bytearray(name, 'ascii'))

response = 0

while response != "name_recived":
    response = sock.recv(1024).decode('ascii')

print("Wait for game start!", file=sys.stdout)

signal = None

while signal != "GameStart":
    signal = sock.recv(1024)
    signal = signal.decode('ascii')
    print(signal)

print("after Gamestart")

input_enable = False

while True:
        data = recv_from_server(sock)
        if "Input_enable" not in data:
            print(data)
        else:
            response = input("Input: ")
            send_to_server(sock, response)
            data = 0
