import socket
from threading import Thread


class CustomProxy():

    def __init__(self, ip="127.0.0.1", backlog=10):
        self.BUFFER_SIZE = 8 * 1024
        self.ip = ip
        self.port = 8080
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        log("Socket successfully created")
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.ip, self.port))
        log("Socket bounded to %s" % self.port)
        self.socket.listen(backlog)
        log("Socket is listening")

        while True:
            client_socket, client_address = self.socket.accept()
            log('Accepted a request from client %s!\n' % str(client_address))
            thread = Thread(target=self.handle_client, args=(client_socket, client_address))
            thread.setDaemon(True)
            thread.start()

    def handle_client(self, client_socket, client_address):
        request = client_socket.recv(self.BUFFER_SIZE)
        request = request.decode("utf-8")
        log("Request received from %s" % str(client_address))
        self.parseRequest(request)

    def parseRequest(self, request):
        splitted_request = request.split('\r\n')

        requested_address = splitted_request[0].split(' ')[1]
        host = splitted_request[1].split(' ')[1]
        path = requested_address[requested_address.find(host) + len(host):]
        splitted_host = host.split(":")
        host_name = splitted_host[0]
        host_port = splitted_host[1] if len(splitted_host) > 1 else 80

        log(splitted_request)
        log("path: %s" % path)
        log("host_name: %s" % host_name)
        log("host_port: %s" % host_port)

        return splitted_request, path, host_name, host_port


def log(message):
    print(message)


CustomProxy()
