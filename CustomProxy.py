import socket
import time
from threading import Thread
import json


class CustomProxy():

    def __init__(self, ip="127.0.0.1", backlog=20, config_file='config.json'):
        self.BUFFER_SIZE = 2 * 1024
        self.ip = ip
        self.log_file = None

        self.set_config(config_file)
        self.log('Configuration setup done.')

        self.log('Proxy launched')
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.log("Socket successfully created")
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.ip, self.port))
        self.log("Socket bounded to %s" % self.port)
        self.socket.listen(backlog)
        self.log("Socket is listening")

        while True:
            client_socket, client_address = self.socket.accept()
            self.log('Accepted a request from client %s\n' % str(client_address))
            thread = Thread(target=self.handle_client, args=(client_socket, client_address))
            thread.setDaemon(True)
            thread.start()

    def set_config(self, config_file):
        config_data = open(config_file).read()
        self.config = json.loads(config_data)
        self.port = self.config['port']
        self.logging = self.config['logging']
        self.caching = self.config['caching']
        self.privacy = self.config['privacy']
        self.restriction = self.config['restriction']
        self.accounting = self.config['accounting']
        self.HTTPInjection = self.config['HTTPInjection']

    def handle_client(self, client_socket, client_address):
        request = client_socket.recv(self.BUFFER_SIZE)
        self.log("Request received from %s[%s] with headers:" % client_address)
        self.log("-----------------------------------\n%s\n-----------------------------------" % request, False)
        method, path, host_name, host_port = self.parse_request(request)
        request = self.update_request(request, method, path)
        response = self.send_request(request, host_name, host_port)
        client_socket.sendall(response)
        self.log("Response sent to %s[%s]" % client_address)

    def parse_request(self, request):
        splitted_request = request.split('\r\n')

        method, requested_address, _ = splitted_request[0].split(' ')
        host = ''
        for line in splitted_request:
            if line.find('Host') != -1:
                host = line.split(' ')[1]
                break
        path = requested_address[requested_address.find(host) + len(host):]
        splitted_host = host.split(":")
        host_name = splitted_host[0]
        host_port = splitted_host[1] if len(splitted_host) > 1 else 80

        return method, path, host_name, host_port

    def update_request(self, request, method, path):
        splitted_request = request.split('\r\n')

        splitted_request[0] = method + " " + path + " HTTP/1.0"
        new_request = ''
        for line in splitted_request:
            if line.find('Proxy-Connection') != -1:
                continue
            if self.privacy['enable'] and line.find('User-Agent') != -1:
                line = 'User-Agent: %s' % self.privacy['userAgent']
            new_request += line + "\r\n"

        return new_request

    def send_request(self, request, host_name, host_port):
        _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.log("Socket to %s[%s] created and connected" % (host_name, host_port))
        _socket.connect((host_name, host_port))
        _socket.sendall(request)
        self.log("Request sent to %s[%s] with headers:" % (host_name, host_port))
        self.log("-----------------------------------\n%s\n-----------------------------------" % request, False)
        response = self.recv_all(_socket)
        self.log("Response received from %s[%s]" % (host_name, host_port))
        _socket.close()
        return response

    def recv_all(self, _socket):
        output = ''
        while True:
            data = _socket.recv(self.BUFFER_SIZE)
            if len(data) > 0:
                output += data
            else:
                break
        return output

    def log(self, message, date=True):
        if self.logging['enable']:
            if self.log_file is None:
                file_name = self.logging['logFile']
                self.log_file = open(file_name, 'a+')
            else:
                current_time = time.strftime('[%d/%m/%Y:%H:%M:%S]')
                if date:
                    self.log_file.write('%s %s\n' % (current_time, message))
                else:
                    self.log_file.write('%s\n' % message)

    def __del__(self):
        self.log("Proxy shutdown")
        self.log(
            "$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$",
            False)


myProxy = CustomProxy()
