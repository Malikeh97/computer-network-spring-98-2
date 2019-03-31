import socket
from threading import Thread


class CustomProxy():

    def __init__(self, ip="127.0.0.1", backlog=10):
        self.BUFFER_SIZE = 1024
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
            log("here")
            thread.setDaemon(True)
            thread.start()

    def handle_client(self, client_socket, client_address):
        request = self.recv_all(client_socket)
        log("Request received from %s" % str(client_address))
        method, path, host_name, host_port = self.parse_request(request)
        request = self.update_request(request, method, path)
        response = self.send_request(request, host_name, host_port)
        client_socket.sendall(response.encode('utf-8', 'ignore'))
        log("Response sent to client %s" % str(client_address))

    def parse_request(self, request):
        splitted_request = request.split('\r\n')

        method, requested_address, _ = splitted_request[0].split(' ')
        host = splitted_request[1].split(' ')[1]
        path = requested_address[requested_address.find(host) + len(host):]
        splitted_host = host.split(":")
        host_name = splitted_host[0]
        host_port = splitted_host[1] if len(splitted_host) > 1 else 80

        log(splitted_request)
        log("path: %s" % path)
        log("host_name: %s" % host_name)
        log("host_port: %s" % host_port)

        return method, path, host_name, host_port

    def update_request(self, request, method, path):
        splitted_request = request.split('\r\n')

        splitted_request[0] = method + " " + path + " HTTP/1.0"
        new_request = ""
        for line in splitted_request:
            if line.find('Proxy-Connection') != -1:
                continue
            new_request += line + "\r\n"

        return new_request

    def send_request(self, request, host_name, host_port):
        _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        log("Socket to server created")
        _socket.connect((host_name, host_port))
        log("Socket connected to server")
        log(request)
        _socket.sendall(request.encode('utf-8', 'ignore'))
        log("request sent to server")
        response = self.recv_all(_socket)
        log(response)
        log("response received")
        _socket.close()
        return response

    def recv_all(self, _socket):
        output = b''
        while True:
            data = _socket.recv(self.BUFFER_SIZE)
            output += data
            if len(data) < self.BUFFER_SIZE:
                break
        return output.decode('utf-8', 'ignore')


def log(message):
    print(message)


CustomProxy()
