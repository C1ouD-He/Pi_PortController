import socket

# 定义服务器地址和端口
HOST = 'localhost'
PORT = 8082

# 创建客户端套接字
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))

while True:
    # 接收用户输入的命令
    command = input('Enter command (subscribe/unsubscribe/exit): ')
    
    # 发送命令给服务器
    client_socket.send(command.encode())

    # 处理服务器的响应
    if command == 'exit':
        break
    else:
        response = client_socket.recv(1024).decode()
        print(f'Server response: {response}')

client_socket.close()