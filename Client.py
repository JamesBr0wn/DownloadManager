import socket
import struct
import os

PACKET_LEN = 1024   # 一个包的大小

# 服务器的ip及端口
server_ip = '127.0.0.1'
server_port = 10086

# 储存文件的路径
download_path = 'D:\\pyCharm\\'


class Client:
    def __init__(self):
        # 连接服务器
        self.connection_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection_socket.connect((server_ip, server_port))

    # 打印列表
    def list(self):
        file_amount_temp = self.connection_socket.recv(4)
        file_amount = struct.unpack('i', file_amount_temp)[0]
        for i in range(file_amount):
            length = self.connection_socket.recv(4)
            message_length = struct.unpack('i', length)[0]
            message = self.connection_socket.recv(message_length).decode()
            print(message)

    # 上传文件
    def upload(self, request):
        try:
            file_name = request[7:]
            file_size = os.path.getsize(file_name)
            head = struct.pack("i", file_size)
            length = struct.pack("i", len(file_name))
            self.connection_socket.send(head)
            self.connection_socket.send(length)
            self.connection_socket.send(file_name.encode())
            file = open(file_name, 'rb')
            packet = file.read(PACKET_LEN)
            while packet:
                self.connection_socket.send(packet)
                packet = file.read(PACKET_LEN)
            file.close()
            length = self.connection_socket.recv(4)
            message_length = struct.unpack("i", length)[0]
            message = self.connection_socket.recv(message_length).decode()
            print(message)
        except:
            print('Error:' + request[7:])

    # 下载文件
    def download(self):
        head = self.connection_socket.recv(4)
        file_size = struct.unpack("i", head)[0]
        if file_size == -1:
            print('Error in this request')
            return
        length = self.connection_socket.recv(4)
        file_name_length = struct.unpack('i', length)[0]
        file_name = self.connection_socket.recv(file_name_length).decode()
        # 检查是否有重名文件，若有，在文件名格式前加上(index)，注意不是文件名的末尾，而是在‘.'前面
        file_final_name = file_name
        index = 1
        while os.path.exists(download_path + file_final_name):
            file_final_name = file_name[:file_name.rfind('.')] + '(' + str(index) + ')' + file_name[file_name.rfind('.'):]
            index = index + 1
        # 接收文件
        file = open(download_path + file_final_name, 'ab')
        receive_size = 0
        while receive_size < file_size:
            packet = self.connection_socket.recv(PACKET_LEN)
            file.write(packet)
            receive_size += len(packet)
        file.close()
        print("Download successfully")
        print("File size:\t" + str(file_size))

    def run(self):
        # 连接成功，访问服务器
        while True:
            try:
                # 提示用户输入命令，并传送该命令给服务器
                request = input("Input your request:\t")
                if request != 'list' and request[:8] != 'download' \
                        and request != 'quit' and request[:6] != 'upload':
                    print("Request unrecognized, please try again!")
                    continue
                self.connection_socket.send(request.encode())
                # 如果用户输入quit，退出程序
                if request == 'quit':
                    print('Connection closed')
                    self.connection_socket.close()
                    break
                # 查询服务器上的文件列表
                elif request == 'list':
                    self.list()
                # 上传文件
                elif request[:6] == 'upload':
                    self.upload(request)
                # download文件：接收文件的大小、文件名称大小及文件名
                else:
                    self.download()
            # 连接过程中突然中断连接
            except socket.error:
                print('Server lost the connection.')
                self.connection_socket.close()
                break


try:
    client = Client()
except:
    print('Connection failed. The server rejects your request.')
else:
    print('Connection established.')
    client.run()
