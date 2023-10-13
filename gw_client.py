import socket
import threading
import time

# 定义服务器地址和端口
HOST = 'localhost'
PORT = 8082

def receiver():
    while onOpened:
        response = client_socket.recv(1024).decode()
        print(f'Server response: {response}')



while True:
    # 接收用户输入的命令
    command = input('Enter command (=n/!n/cc): ')
    
    
    if command[0] == '=':
        # 创建客户端套接字
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((HOST, PORT))
        onOpened = True
        thread = threading.Thread(target=receiver, daemon=True)
        thread.start()
        command = 'ttyUSB' + command[-1]
    # 处理服务器的响应
    elif command[0] == '!':
        command = 'unsubscribettyUSBn' + command[-1]
    elif command == 'cc':
        command = 'Client closed'
        client_socket.send(command.encode())
        onOpened = False
        time.sleep(0.5)
        client_socket.close()
        continue

    # 发送命令给服务器
    client_socket.send(command.encode())
