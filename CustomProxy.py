import socket
import time
from threading import Thread
import json

UNAVAILABLE = 0
EXPIRED = 1
FRESH = 2


class Cache():
    def __init__(self, cache_enable, cache_size):
        self.cache_enable = cache_enable
        self.cache_size = cache_size
        self.cache_dict = {}
    # def is_expired(self, path, host_name, host_port):

    # def data_status(self, path, host_name, host_port):
    #     if not self.cache_dict.has_key(host_name+path+":"+str(host_port)):
    #         return UNAVAILABLE
    #     else:
    #         if





class CustomProxy():

    def __init__(self, ip="127.0.0.1", backlog=20, config_file='config.json'):
        self.BUFFER_SIZE = 2 * 1024
        self.ip = ip

        self.set_config(config_file)
        self.log('Configuration setup done.')

        self.cache = Cache(self.caching['enable'], self.caching['size'])
        self.log("Cache is set up")

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
        client_packet = self.handle_caching(request, path, host_name, host_port)
        response = self.send_request(request, host_name, host_port) #tobe combined
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
        new_request = ""
        for line in splitted_request:
            if line.find('Proxy-Connection') != -1:
                continue
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
        current_time = time.strftime("[%d/%m/%Y:%H:%M:%S]")
        if date:
            print('%s %s' % (current_time, message))
        else:
            print(message)

    def check_request_header(self, data):

        data_is_stale = True
        if_modified_since = False
        no_cache = False
        no_store = False
        # check_modified = False

        request_header = data.split('\n')
        for element in request_header:

            if element == '':  # check in headers
                break

            if 'If-Modified-Since' in element:
                if_modified_since = True
                # check_modified = True

            if 'Cache-Control' in element:
                tmp = element.split(':')[1]
                params = tmp.split(',')
                for param in params:
                    if 'no-cache' in param:
                        no_cache = True

                    if 'no-store' in param:
                        no_store = True

        return if_modified_since, no_cache, no_store

    def handle_caching(self, request, path, host_name, host_port):

        cache_response = ''

        if self.caching['enable'] == True:

            if_modified_since, no_cache, no_store = self.check_request_header(request)



            # data_status = redis_obj.ttl(self.url)
            #
            # if data_status == -2:  # the source not available in cache
            #     check_modified = False
            #     data_is_stale = True
            #
            # elif data_status == -1:  # the source is expired
            #     check_modified = True
            #     data_is_stale = True
            #
            # elif data_status >= 0:  # the source is fresh
            #     data_is_stale = False
            #
            # # get data from server or use cache
            # if data_is_stale == False:
            #     log('get from redis\n')
            #     print 'get from redis '
            #     cache_response = redis_obj.get(self.url)
            #
            # if data_is_stale == True:
            #     cache_response = self.handle_server_response(check_modified, has_if_modified_since, request, webserver,
            #                                                  port)

        # else:
        #     cache_response = self.send_to_server(request, webserver, port)
        return cache_response


myProxy = CustomProxy()
