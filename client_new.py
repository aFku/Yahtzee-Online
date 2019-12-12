import socket
import sys

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

while signal == "GameStart":
    signal = sock.recv(1024)
    signal = signal.decode('ascii')

input_enable = True

while True:
    data = sock.recv(1024)
    if data.decode('ascii') == "FIN":
        input_enable = False
    elif data.decode('ascii') == "START":
        input_enable = True
    elif data:
        print(data.decode('ascii'))
        print("\n Wait for your turn!")
    if input_enable:
        action = input("Your choice: ")
        sock.sendall(bytearray(action, 'ascii'))






