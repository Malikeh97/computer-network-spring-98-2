import socket
from threading import Thread


class CustomProxy():

    def __init__(self, ip="127.0.0.1", backlog=10):
        self.ip = ip
        self.port = "8080"
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        log("Socket successfully created")
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.ip, self.port))
        log("Socket bounded to %s" % self.port)
        self.socket.listen(backlog)
        log("Socket is listening")

        while True:
            client_socket, client_address = self.socket.accept()
            log('Accepted a request from client %s!\n' % client_address)
            thread = Thread(target = self.handle_client, args=(client_socket, client_address))
            thread.setDaemon(True)
            thread.start()

    def handle_client(self, client_socket, client_address):
        log("handle client")

def log(message):
    print(message)
