import socket
import sys

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_address = ("localhost", 10000)

print("Connecting to server", file=sys.stdout)

sock.connect(server_address)

while True:
    while True:
        message = input("Put your message here: ")
        if message:
            sock.sendall(bytearray(message, 'ascii'))
            break
    while True:
        data = sock.recv(1024)
        if data:
            print(data.decode("ascii"), file=sys.stdout)
            break
