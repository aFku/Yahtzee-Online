import socket
import sys


def bind_address(address, sock):
    try:
        sock.bind(address)
    except:
        print("Can`t bind address", file=sys.stderr)
        exit()
    else:
        print("Server is binded to address %s on port %s" % address, file=sys.stdout)




if __name__ == "__main__":
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_address = ("localhost", 10000)
    bind_address(server_address, sock)

    sock.listen(1)

    print("Waiting for connection", file=sys.stdout)

    connections = {}

    while True:
        connection, client_address = sock.accept()
        if len(client_address) != 0:
            client_address = client_address[0] + ":" + str(client_address[1])
            connections[client_address] = connection
            print("connection from %s", client_address, file=sys.stdout)

        if len(connections.items()) == 2:
            break

    print("Accepted two connections", file=sys.stdout)
    keys = connections.items()
    tmp = []
    for x in keys:
        tmp.append(x[0])
    keys = tmp
    del tmp
    while True:
        data1 = connections[keys[0]].recv(1024)
        data2 = connections[keys[1]].recv(1024)
        if data1:
            connections[keys[1]].sendall(data1)
        if data2:
            connections[keys[0]].sendall(data2)





