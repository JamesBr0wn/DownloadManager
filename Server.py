import socket
import struct
import os
import threading

PACKET_LEN = 1024   # 一个包的大小
THREAD_NUM= 8       # 可同时建立TCP连接数

upload_path = ''  # 储存文件的路径


class Server:
    def __init__(self, server_ip, server_port):
        self.server_port = server_port
        self.server_ip = server_ip
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def serve(self):
        self.server_socket.bind((self.server_ip, self.server_port))
        self.server_socket.listen(THREAD_NUM)
        while True:
            connection_socket, client_addr = self.server_socket.accept()
            thread = threading.Thread(target=self.connect, args=(connection_socket, client_addr))
            thread.start()
            thread.join()

    @staticmethod
    def connect(connection_socket, client_addr):
        cont = Connection(connection_socket, client_addr)
        cont.serve()


class Connection:
    def __init__(self, connection_socket, client_addr):
        self.connection_socket = connection_socket
        self.client_addr = client_addr
        with open('file_list.txt') as file_object:
            lines = file_object.readlines()
        self.file_number = len(lines) + 1  # 文件数量+1，用于指向文件末尾行

    def serve(self):
        print("Client " + str(self.client_addr) + " connected.")
        while True:
            try:
                request = self.connection_socket.recv(1024).decode()
                if request[:4] == 'list':
                    print('Request: ' + request + ' From: ' + str(self.client_addr))
                    self.file_list()
                elif request[:8] == 'download':
                    print('Request: ' + request + ' From: ' + str(self.client_addr))
                    try:
                        self.file_down(int(request[8:]))
                    except:
                        error = struct.pack("i", -1)
                        self.connection_socket.send(error)
                elif request[:4] == 'quit':
                    print('Client  ' + str(self.client_addr) + ' disconnected.')
                    self.connection_socket.close()
                    break
                elif request[:6] == 'upload':
                    self.file_up()
                elif request[:4] == '':
                    continue
                else:
                    print('Client ' + str(self.client_addr) + ' has illegal request, connection closed!')
                    self.connection_socket.close()
                    break
            except socket.error:
                print('Client ' + str(self.client_addr) + ' lost the connection.')
                self.connection_socket.close()
                break

    def file_up(self):
        # 读取文件信息
        head = self.connection_socket.recv(4)
        file_size = struct.unpack("i", head)[0]
        length = self.connection_socket.recv(4)
        file_name_length = struct.unpack('i', length)[0]
        file_name = self.connection_socket.recv(file_name_length).decode()
        # 检查是否有重名文件，若有，在文件名格式前加上(index)，注意不是文件名的末尾，而是在‘.'前面
        file_final_name = file_name
        index = 1
        while os.path.exists(upload_path + file_final_name):
            file_final_name = file_name[:file_name.rfind('.')] + '(' + str(index) + ')' + file_name[
                                                                                          file_name.rfind('.'):]
            index = index + 1
        # 接收文件
        file = open(upload_path + file_final_name, 'ab')
        receive_size = 0
        while receive_size < file_size:
            packet = self.connection_socket.recv(PACKET_LEN)
            file.write(packet)
            receive_size += len(packet)
        file.close()
        # 新添文件名至查询表
        with open('file_list.txt', 'a') as file_object:
            file_object.write(str(self.file_number) + ' ' + file_final_name + '\n')
        self.file_number = self.file_number + 1
        message = "Upload successfully."
        message_length = struct.pack('i', len(message))
        self.connection_socket.send(message_length)
        self.connection_socket.send(message.encode())
        print("Upload file:" + file_final_name)
        print("File size:\t" + str(file_size))

    # 打开文件记录表，将里面的信息发送给客户端
    def file_list(self):
        file_name = 'file_list.txt'
        file_amount = struct.pack("i", self.file_number - 1)
        self.connection_socket.send(file_amount)
        with open(file_name) as file_object:
            for line in file_object:
                length = struct.pack("i", len(line.rstrip()))
                self.connection_socket.send(length)
                self.connection_socket.send(line.rstrip().encode())

    # 客户端请求下载文件
    def file_down(self, file_index):
        try:
            file = open('file_list.txt', 'r')
            file_list = file.readlines()
            file_name = file_list[file_index - 1].split(' ')[1].rstrip()
            file.close()
            self.send_file_info(file_name)
            self.send_file(file_name)
        except:
            error = struct.pack("i", -1)
            self.connection_socket.send(error)

    # 发送文件的信息给客户端
    def send_file_info(self, file_name):
        file_size = os.path.getsize(file_name)
        head = struct.pack("i", file_size)
        length = struct.pack("i", len(file_name))
        self.connection_socket.send(head)
        self.connection_socket.send(length)
        self.connection_socket.send(file_name.encode())

    # 发送文件给客户端
    def send_file(self, file_name):
        file = open(file_name, 'rb')
        packet = file.read(PACKET_LEN)
        while packet:
            self.connection_socket.send(packet)
            packet = file.read(PACKET_LEN)


server = Server('0.0.0.0', 10086)
server.serve()
