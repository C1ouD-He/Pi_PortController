import sys
import readchar
import socket
import threading
import asyncio
import subprocess

def get_local_ip():
    """
    获取本地 IP 地址
    """
    # 创建一个 UDP socket 对象
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # 连接到一个公共 IP 地址
        sock.connect(('8.8.8.8', 80))
        # 获取本地 IP 地址
        local_ip = sock.getsockname()[0]
    except Exception as e:
        print(f"获取本地 IP 地址失败：{e}")
        local_ip = None
    finally:
        # 关闭 socket 连接
        sock.close()
    return local_ip

class Port_Client(object):
    def __init__(self):
        # 定义服务器地址和端口
        self.HOST = get_local_ip()
        self.PORT = 8082
        self.onOpened = False
        self.onConnected = False
        self.mcu_project = ''
        self.soc_commond = False
        self.input_tmp = ''
        self.tab_state = False
        self.tab_option = []
        self.tab_tmp = ''
        self.inputHead = ''
        self.run_connecting()

    async def receiver(self):
        # self.client_socket.settimeout(0.05)
        print(f'INFO: Receiver[{self.connName}] open!')
        while self.onOpened:
            try:
                response = self.client_socket.recv(1).decode()
                sys.stdout.write(response)
                sys.stdout.flush()
            except socket.timeout:
                self.tab_state = False     # tab finish
                pass
            except ConnectionRefusedError:
                await self.onConnectFail()
            except OSError:
                await self.onConnectFail()
        print(f'INFO: Receiver[{self.connName}] close!')

    def run_receiver(self):
        asyncio.run(self.receiver())

    async def sender(self):                                            # send the subscribe message
        self.client_socket.send(self.connName.encode())
        print(f'INFO: Subscribe[{self.connName}]!')
        self.onOpened = True
        self.thread_rcver = threading.Thread(target=self.run_receiver, daemon=True)
        self.thread_rcver.start()
        try:
            self.client_socket.send(chr(0x0D).encode())
            await asyncio.sleep(0.7)
        except BrokenPipeError:
            await self.onConnectFail()
        except ConnectionRefusedError:
            await self.onConnectFail()
        except OSError:
            await self.onConnectFail()
        if self.onOpened == False:
            return
        while True:
            try:
                command = readchar.readkey()
                if self.tab_tmp != '':           # if tab,clear the content before tab
                    command = command[len(self.tab_tmp):]
                    self.tab_tmp = ''
                #if command == '':
                #    self.client_socket.send(chr(0x0D).encode())
                #    break
                elif command == chr(0x0F): # 'q' or command == 'Q':
                    command = 'unsubscribe' + self.connName
                    self.onOpened = False
                    print(f'INFO: Unsubscribe[{self.connName}]!')
                    self.client_socket.send(command.encode())   # send the unsubscribe message
                    await asyncio.sleep(0.11)
                    return
                else:
                    # 发送命令给服务器
                    self.client_socket.send(command.encode())
                    self.input_tmp = command
                    command = ''
            except KeyboardInterrupt:
                if self.onOpened:
                    self.client_socket.send(chr(0x03).encode())
                else:
                    return
            except BrokenPipeError:
                await self.onConnectFail()
            except ConnectionRefusedError:
                await self.onConnectFail()
            except OSError:
                await self.onConnectFail()

            if self.onOpened == False:
                return

    def port_terminal(self):            # index select session
        self.help()
        while True:
            InputB = input('choose ( 0 ~ 9 | svrlog | ipport | chip | chport | quit | -h)->')
            if(InputB == 'quit') or (InputB == 'QUIT'):
                print('INFO: Port Client closed!')
                exit()
            elif InputB == 'ipport':
                print(f'INFO: IP setting: {self.HOST}:{self.PORT}')
                continue  
            elif InputB == 'chip':
                print(f'INFO: IP is {self.HOST}')
                self.HOST = input('Please enter IP:')
                print('INFO: IP change success!')
                print(f'INFO: IP setting: {self.HOST}:{self.PORT}')
                self.onOpened = False
                self.onConnected = False
                self.client_socket.close()
            elif InputB == 'chport':
                print(f'INFO: PORT is {self.PORT}')
                try:
                    self.PORT = int(input('Please enter PORT:'))
                    print('INFO: PORT change success!')
                    print(f'INFO: IP setting: {self.HOST}:{self.PORT}')
                except ValueError:
                    print('ERROR: Port num error!')
                self.onOpened = False
                self.onConnected = False
                self.client_socket.close()
            elif InputB == '-h':
                self.help()
                continue
            if self.onConnected == False:
                if InputB != '':
                    self.run_connecting()
            if self.onConnected == True:
                if InputB == '' or InputB == 'ipport' or InputB == 'chip' or InputB == 'chport':
                    continue
                elif InputB == 'svrlog':
                    pass
                else:
                    try:
                        InputB = int(InputB)
                        for i in range(10):
                            if InputB == i:
                                InputB = 'ttyUSB' + str(InputB)
                                break
                    except ValueError:
                        print('WARNING: Input out of list!')
                        continue
                self.connName = InputB
                asyncio.run(self.sender())

    def run_port_terminal(self):
        try:
            self.port_terminal()
        except KeyboardInterrupt:
            self.onOpened = False
            self.client_socket.close()

    async def onConnectFail(self):
        if self.onOpened == False:
            return
        self.onOpened = False
        self.onConnected = False
        self.client_socket.close()
        for i in range (5):
            print(f'Error: Connection failed! ReConnecting{i+1} ...')
            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.connect((self.HOST, self.PORT))
                self.onOpened = True
                self.onConnected = True
                print('INFO: ReConnecting success!')
                self.thread_rcver = threading.Thread(target=self.run_receiver, daemon=True)     # while reconnect success before back to index page,restart the receiver
                self.thread_rcver.start()
                self.client_socket.send(self.connName.encode())
                return
            except ConnectionRefusedError:
                await asyncio.sleep(3)
            except OSError:
                await asyncio.sleep(3)
        print('Error: Connection failed!')

    async def connecting(self):
        for i in range(5):
            print(f'INFO: Connecting{i+1}...')
            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.settimeout(3)
                self.client_socket.connect((self.HOST, self.PORT))
                self.onOpened = True
                self.onConnected = True
                print('INFO: Connecting success!')
                return
            except socket.timeout:
                pass
            except ConnectionRefusedError:
                await asyncio.sleep(3)
            except OSError:
                await asyncio.sleep(3)
        print('Error: Connection failed!')

    def run_connecting(self):
        try:
            asyncio.run(self.connecting())
        except KeyboardInterrupt:
            print('\nINFO: Connection broken!')
        except TypeError:
            print('ERROR: IP setting error! Please check!')
        
    def run(self):
        self.run_port_terminal()

    def print_help(self, txt):
        print('\033[;;100m' + txt + '\033[0m')

    def help(self):
        self.print_help('|---------------------------------------------------------|')
        self.print_help('|----------------------#HELP -v2.3.0----------------------|')
        self.print_help('|                                                         |')
        self.print_help('| input 0 ~ 9 to choose ttyUSB0~9                         |')
        self.print_help('| input svrlog to grep server log                         |')
        self.print_help('| input ipport to show ip setting                         |')
        self.print_help('| input chip to change ip                                 |')
        self.print_help('| input chport to change port                             |')
        self.print_help('| input quit to quit the program                          |')
        self.print_help('|                                                         |')
        self.print_help('| when using serial:                                      |')
        self.print_help('| input Ctrl+O will return to choosing conn port          |')
        self.print_help('|                                                         |')
        self.print_help('|                                                         |')
        self.print_help('|---------------------------------------------------------|')


def run_shell(alias_name):
    result = subprocess.run(alias_name, shell=True)
    print(result)

if __name__ == '__main__':
    # 调用别名为 pwr 的命令
    # run_shell('sudo /usr/bin/python3.7 /home/pi/.remote_env/ea_psu_ctrl.py')

    port_client = Port_Client()
    port_client.run()
