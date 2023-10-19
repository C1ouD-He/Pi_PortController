import socket
import threading
import time

class Gw_Client(object):
    def __init__(self):
        # 定义服务器地址和端口
        self.HOST = 'localhost'
        self.PORT = 8082
    def receiver(self):
        while self.onOpened:
            response = self.client_socket.recv(1024).decode()
            print(response)

    def sender(self):
        while True:
            # 接收用户输入的命令
            command = input('Enter command (=n/!n/cc): ')
            if command[0] == '=':
                # 创建客户端套接字
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.connect((self.HOST, self.PORT))
                self.onOpened = True
                self.thread_rcver = threading.Thread(target=self.receiver, daemon=True)
                self.thread_rcver.start()
                command = 'ttyUSB' + command[-1]
            # 处理服务器的响应
            elif command[0] == '!':
                command = 'unsubscribettyUSBn' + command[-1]
            elif command == 'cc':
                command = 'Client closed'
                self.client_socket.send(command.encode())
                self.onOpened = False
                self.client_socket.close()
                continue

            # 发送命令给服务器
            self.client_socket.send(command.encode())

    def run(self):
        self.sender()


if __name__ == '__main__':
    gw_client = Gw_Client()
    gw_client.run()
