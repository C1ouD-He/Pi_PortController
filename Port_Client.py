import sys
import readchar
import socket
import threading
import asyncio
# import colorama
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
        self.thread_rcver = None
        self.client_socket = None
        self.connName = None
        self.HOST = None
        # colorama.init(convert=True)
        # 定义服务器地址和端口
        self.chip()
        self.PORT = 8082
        self.onOpened = False
        self.onConnected = False
        self.input_tmp = ''
        self.run_connecting()

    async def receiver(self):
        self.client_socket.settimeout(0.1)
        print(f'INFO: Receiver[{self.connName}] open!')
        while self.onOpened:
            try:
                response = self.client_socket.recv(1).decode()
                sys.stdout.write(response)
                sys.stdout.flush()
            except socket.timeout:
                pass
            except ConnectionRefusedError:
                await self.onConnectFail()
            except OSError:
                await self.onConnectFail()
        print(f'INFO: Receiver[{self.connName}] close!')

    def run_receiver(self):
        asyncio.run(self.receiver())

    async def sender(self):  # send the subscribe message
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
        if not self.onOpened:
            return
        while True:
            try:
                command = readchar.readkey()
                if command == chr(0x0F):  # Ctrl+O:
                    command = 'unsubscribe' + self.connName
                    self.onOpened = False
                    self.client_socket.send(command.encode())  # send the unsubscribe message
                    print(f'INFO: Unsubscribe[{self.connName}]!')
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

            if not self.onOpened:
                return

    def port_terminal(self):  # index select session
        self.help()
        while True:
            tx = input('>>')
            if (tx == 'quit') or (tx == 'QUIT'):
                print('INFO: Port Client closed!')
                exit()
            elif tx == 'ipport':
                print(f'INFO: IP setting: {self.HOST}:{self.PORT}')
                continue
            elif tx == 'chip':
                print(f'INFO: IP is {self.HOST}')
                self.chip()
                print('INFO: IP change success!')
                print(f'INFO: IP setting: {self.HOST}:{self.PORT}')
                self.onOpened = False
                self.onConnected = False
                self.client_socket.close()
            elif tx == 'chport':
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
            elif tx == '-h':
                self.help()
                continue
            if not self.onConnected:
                if tx != '':
                    self.run_connecting()
            if self.onConnected:
                if tx == '' or tx == 'ipport' or tx == 'chip' or tx == 'chport':
                    continue
                elif tx == 'svrlog':
                    pass
                else:
                    try:
                        tx = int(tx)
                        for i in range(10):
                            if tx == i:
                                tx = 'ttyUSB' + str(tx)
                                break
                    except ValueError:
                        print('WARNING: Input out of list!')
                        continue
                self.connName = tx
                asyncio.run(self.sender())

    def run_port_terminal(self):
        try:
            self.port_terminal()
        except KeyboardInterrupt:
            self.onOpened = False
            self.client_socket.close()

    async def onConnectFail(self):
        if not self.onOpened:
            return
        self.onOpened = False
        self.onConnected = False
        self.client_socket.close()
        for i in range(5):
            print(f'Error: Connection failed! ReConnecting {i + 1} ...')
            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.connect((self.HOST, self.PORT))
                self.onOpened = True
                self.onConnected = True
                print('INFO: ReConnecting success!')
                self.thread_rcver = threading.Thread(target=self.run_receiver,
                                                     daemon=True)  # while reconnect success before back to index page,restart the receiver
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
            print(f'INFO: Connecting {i + 1} ...')
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

    @staticmethod
    def print_help(txt):
        print(txt)
        # print(colorama.Back.LIGHTBLACK_EX + txt + colorama.Back.RESET)

    def chip(self):
        ip = input('Server IP(Enter nothing to use local ip):')
        if ip == '':
            self.HOST = get_local_ip()
        else:
            self.HOST = ip

    def help(self):
        self.print_help('|---------------------------------------------------------|')
        self.print_help('|----------------------#HELP -v2.3.2----------------------|')
        self.print_help('|                                                         |')
        self.print_help('| [0] ~ [9]      to choose ttyUSB0~9                      |')
        self.print_help('| [svrlog]       to grep server log                       |')
        self.print_help('| [ipport]       to show ip setting                       |')
        self.print_help('| [chip]         to change ip                             |')
        self.print_help('| [chport]       to change port                           |')
        self.print_help('| [-h]           to help                                  |')
        self.print_help('| [quit]         to quit the program                      |')
        self.print_help('|                                                         |')
        self.print_help('| when using serial:                                      |')
        self.print_help('|      [Ctrl + O] will return to index line               |')
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
