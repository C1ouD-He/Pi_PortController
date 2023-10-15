import os
import socket
import threading
import asyncio

class Port_Client(object):
    def __init__(self):
        # 定义服务器地址和端口
        self.HOST = 'localhost'
        self.PORT = 8082
        # 创建客户端套接字
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.HOST, self.PORT))
        self.onOpened = True

        self.mcu_project = ''
        self.soc_commond = False
        self.input_tmp = ''
        self.echo = False

    # 删除前一条历史记录的函数
    def delete_previous_history(self):
        index = self.readline.get_current_history_length() - 1
        try:
            self.readline.remove_history_item(index)
        except ValueError:
            pass
    
    def clear_terminal(self):
        self.delete_previous_history()
        self.readline.write_history_file(self.histfile)
        self.readline.clear_history()
        os.chmod(self.histfile, 0o666)
        # del self.readline

    def receiver(self):
        self.client_socket.settimeout(0.1)
        print('INFO: Receiver open!')
        while self.onOpened:
            try:
                response = self.client_socket.recv(1024).decode()
                if response != '' and (response != (self.input_tmp) or self.echo):   # echo control
                    if(response == '#'):
                        self.soc_commond = True
                    elif 'MCU:' in response[:15]:
                        self.soc_commond = False
                        self.mcu_project = response
                    else:
                        print(response)
            except socket.timeout:
                pass
        print('INFO: Receiver close!')

    async def sender(self, n):
        command = 'ttyUSB' + n                                              # send the subscribe message
        self.client_socket.send(command.encode())
        print(f'INFO: Subscribe ttyUSB{n}!')
        self.onOpened = True
        self.thread_rcver = threading.Thread(target=self.receiver, daemon=True)
        self.thread_rcver.start()
        self.client_socket.send(chr(0x0D).encode())
        await asyncio.sleep(0.7)
        
        import readline
        self.readline = readline

        self.histfile = f'/home/pi/.remote_env/Pi_PortController/.port_history{n}'
        try:
            self.readline.read_history_file(self.histfile)
        except FileNotFoundError:
            # 如果历史记录文件不存在，则创建一个空文件
            open(self.histfile, 'wb').close()
        
        self.readline.set_history_length(1000)

        self.readline.clear_history()
        self.readline.read_history_file(self.histfile)

        while True:
            try:
                # 接收用户输入的命令
                if(self.soc_commond == False):
                    command = input(self.mcu_project)
                else:
                    command = input('# ')
                if command == '':
                    self.client_socket.send(chr(0x0D).encode())
                    continue
                elif command == 'q' or command == 'Q':
                    command = 'unsubscribettyUSB' + n
                    self.onOpened = False
                    self.echo = False
                    self.clear_terminal()
                    print(f'INFO: Unsubscribe ttyUSB{n}!')
                    self.client_socket.send(command.encode())   # send the unsubscribe message
                    await asyncio.sleep(0.11)
                    return
                elif(command == 'echo on'):
                    if(self.echo == False):
                        print('INFO: echo on!')
                    self.echo = True
                elif(command == 'echo off'):
                    if(self.echo == True):
                        print('INFO: echo off!')
                    self.echo = False
                else:
                    # 发送命令给服务器
                    self.client_socket.send(command.encode())
                    self.input_tmp = command
                    command = ''
            except KeyboardInterrupt:
                    self.client_socket.send(chr(0x03).encode())
            except BrokenPipeError:
                self.onConnectFail()

    def port_terminal(self):            # index select session
        while True:
            InputB = input('choose port( 0 ~ 9 | quit | h)->')
            if(InputB == 'quit') or (InputB == 'QUIT'):
                print('INFO: Port Client closed!')
                exit()
            elif InputB == 'h':
                self.help()
            else:
                if InputB == '':
                    continue
                try:
                    InputB = int(InputB)
                except ValueError:
                    print('WARNING: Input out of list!') 
                for i in range(10):
                    if InputB == i:
                        asyncio.run(self.sender(str(InputB)))
                        return
                
        # asyncio.run(self.serial_terminal())

    def port_controller(self):
        try:
            while 1:
                self.port_terminal()
        except KeyboardInterrupt:
            self.onOpened = False
            self.client_socket.close()

    def help(self):
        self.print_help('|---------------------------------------------------------|')
        self.print_help('|----------------------#help -v2.1.4----------------------|')
        self.print_help('|                                                         |')
        self.print_help('| input 0 ~ 9 to choose ttyUSB0~9                         |')
        self.print_help('| input quit to quit the program                          |')
        self.print_help('|                                                         |')
        self.print_help('| when using serial:                                      |')
        self.print_help('| input q will return to choosing port                    |')
        self.print_help('| input echo on/off to enable/disable the echo            |')
        self.print_help('|                                                         |')
        self.print_help('|                                                         |')
        self.print_help('|---------------------------------------------------------|')

    def print_help(self, txt):
        print('\033[;;100m' + txt + '\033[0m')

    def onConnectFail(self):
        self.onOpened = False
        self.client_socket.close()
        while True:
            self.client_socket.connect((self.HOST, self.PORT))

    def run(self):
        self.port_controller()


if __name__ == '__main__':
    port_client = Port_Client()
    port_client.run()
