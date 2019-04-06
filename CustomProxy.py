import socket
import time
from threading import Thread
import json
import collections
import datetime


UNAVAILABLE = 0
EXPIRED = 1
FRESH = 2


class Cache():
    def __init__(self, cache_enable, cache_size):
        self.cache_enable = cache_enable
        self.cache_size = cache_size
        self.data_dict = collections.OrderedDict()
        self.expire_dict = collections.OrderedDict()
        self.tm = 0
        self.lru = {}

    def get_response(self, path, host_name, host_port):
        key = host_name+path
        try:
            value = self.data_dict.pop(key)
            self.data_dict[key] = value
            return value
        except KeyError:
            return -1

    def set_response(self, path, host_name, host_port, server_response, expire_date):
        key = host_name+path
        if len(self.data_dict) >= self.data_dict:
            # find the LRU entry
            old_key = min(self.lru.keys(), key=lambda k:self.lru[k])
            self.data_dict.pop(old_key)
            self.expire_dict.pop(old_key)
            self.lru.pop(old_key)
        self.data_dict[key] = server_response
        self.expire_dict[key] = expire_date
        self.lru[key] = self.tm
        self.tm += 1



    def is_expired(self, path, host_name, host_port): #to do by age or GMT date?!!!!!!
        key = host_name + path
        if not self.expire_dict.has_key(host_name + path):
            return False
        else:
            if self.expire_dict[key] == '':
                return False
            else:
                tmp = datetime.datetime.utcnow()
                cur_date1 = tmp.strftime("%a, %d %b %Y %H:%M:%S GMT")
                expire_date1 = self.expire_dict[key]
                cur_date = datetime.datetime.strptime(cur_date1, '%a, %d %b %Y %H:%M:%S GMT')
                expire_date = datetime.datetime.strptime(expire_date1[1:], '%a, %d %b %Y %H:%M:%S GMT')
                return expire_date < cur_date
        return False

    def data_status(self, path, host_name, host_port):
        if not self.data_dict.has_key(host_name+path):
            return UNAVAILABLE
        else:
            if self.is_expired(path, host_name, host_port):
                return EXPIRED
            else:
                return FRESH
        return FRESH




def add_if_modified_since(server_packet, modify_date):

    line2_pos = server_packet.find('Host')
    end_line_pos = server_packet.find("\r\n", line2_pos) + 2
    part1 = server_packet[:end_line_pos]
    part2 = 'If_Modified_Since:'+ modify_date
    part3 = server_packet[end_line_pos + 1:]

    return part1 + part2 + part3

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
        response = self.handle_caching(request, path, host_name, host_port)
        #response = self.send_request(request, host_name, host_port) #tobe combined
        client_socket.sendall(response)
        self.log("Response sent to %s[%s]" % client_address)

    def parse_request(self, request):
        splitted_request = request.split('\r\n')

        method, requested_address, _ = splitted_request[0].split(' ')
        host = ''
        for line in splitted_request:
            if line.find('Host') != -1:
                if line == '':
                    break
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

    def check_request_header(self, request): #checked!!
        if_modified_since = False
        request_header = request.split('\n')
        for element in request_header:

            if element == '':  # check in headers
                break

            if 'If-Modified-Since' in element:
                if_modified_since = True
                modify_date = element.split(':')[1]

        return if_modified_since, modify_date;

    def check_response_header(self, response): #how to handle expire date and no cache to be considered later !!!!!!
        response_header = response.split('\n')
        no_cache = False
        expire_date = ''
        for element in response_header:
            if element == '':  # check in headers
                break
            if 'Cache-Control' in element:
                tmp = element.split(':')[1]
                params = tmp.split(',')
                for param in params:
                    if 'no_cache' in param:
                        no_cache = True
            if 'Expires' in element:
                expire_date = element.split(':')[1]

        return expire_date, no_cache


    def check_status(self, server_response):
        first_line = server_response.split('\n')[0]
        status = first_line.split(' ')[1]
        if status == '200':
            return True
        if status == '304':
            return False

    def handle_server_response(self, not_in_cache, is_expired, if_modified_since, modify_date, request, path, host_name, host_port):
        server_response = ''
        if_modified = False
        if not if_modified_since : # Request reponse again
            server_response = self.send_request(request, host_name, host_port)
            expire_date, no_cache = self.check_response_header(server_response)
            if_modified = True
            self.log(' Get response from server with no modification check\n')

        else: # Request with if_modified_since header
            request = add_if_modified_since(request, modify_date)
            self.log('Add "if modified since" to the request to server\n')

            server_response = self.send_request(request, host_name, host_port) #send updated request to server
            expire_date, no_cache = self.check_response_header(server_response)
            if_modified = self.check_status(server_response)

        if self.caching['enable'] == True or no_cache == False:

            if if_modified: # update cache & send new to client
                self.log(' Data is modified, update the cache\n')
                output = server_response
                self.cache.set_response(path, host_name, host_port, server_response, expire_date)

            else :# use cache
                self.log(' Data is not modified get from cache \n')
                output = self.cache.get_response(path, host_name, host_port)

        else:
                output = server_response
        return output

    def handle_caching(self, request, path, host_name, host_port):
        if_modified = False
        is_expired = False
        not_in_cache = True


        if self.caching['enable'] == True:

            if_modified, modify_date = self.check_request_header(request)

            data_status = self.cache.data_status(path, host_name, host_port)

            self.log("data_status: "+ str(data_status))

            if data_status == UNAVAILABLE:
                not_in_cache = True

            elif data_status == EXPIRED:
                is_expired = True
                not_in_cache = True

            elif data_status == FRESH:
                not_in_cache = False

            if not_in_cache == False and if_modified == False:
                self.log('Get response from cache\n')
                cache_response = self.cache.get_response(path, host_name, host_port)

            else :
                cache_response = self.handle_server_response(not_in_cache, is_expired, if_modified, modify_date, request, path, host_name, host_port)

        else:
            cache_response = self.send_request(request, host_name, host_port)
        return cache_response


myProxy = CustomProxy()
