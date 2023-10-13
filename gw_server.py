import sys
import os
import re
import time
import asyncio
import threading
import serial
import pyudev
import socket

class serial_terminal(object):
    def __init__(self,n):
        self.n = n
        import readline
        self.readline = readline
        self.input_tmp = ''
        self.echo = False
        self.mcu_project = ''
        self.soc_commond = False
        self.last_cmd = ''
        # self.InputA = ''
        # self.ser = []
        self.log_tmp = ''
        self.status = True
        self.subscribe_client = []
        try:
            self.conn = serial.Serial(f'/dev/ttyUSB{self.n}', baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=0.5)
            self.start_log_reading()
        except serial.serialutil.SerialException:
            print(f'ERROR: ttyUSB{self.n} undetected!')
            self.status = False

        self.histfile = f'/home/pi/.remote_env/Pi_PortController/.port_history_ttyUSB{self.n}'
        # self.histfile = '/home/pi/.remote_env/port/port2.0/.port_history'
        # os.chmod(self.histfile, 0o666)
        # 读取历史记录文件
        try:
            self.readline.read_history_file(self.histfile)
        except FileNotFoundError:
            # 如果历史记录文件不存在，则创建一个空文件
            open(self.histfile, 'wb').close()
        
        self.readline.set_history_length(1000)


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

    # self.readline.set_completer(completer)
    # self.readline.parse_and_bind("tab: complete")

    def start_log_reading(self):
        try:
            self.conn.open()
        except serial.serialutil.SerialException:
            pass
        Serial_Ctrl_Center.onOpened[self.n] = True
        tlog = threading.Thread(target=self.log_reading, daemon=True)  # 开启log监听线程
        tlog.start()

    # log监听线程
    def log_reading(self):
        while Serial_Ctrl_Center.onOpened[self.n]:
            try:
                self.log_tmp = self.conn.readline().decode().strip()
                self.conn.flushOutput()
                if self.log_tmp != '' and (self.log_tmp != (self.input_tmp) or self.echo):   # echo control
                    if(self.log_tmp == '#'):
                        self.soc_commond = True
                    elif 'MCU:' in self.log_tmp:
                        self.soc_commond = False
                        self.mcu_project = self.log_tmp
                    else:
                        print(self.log_tmp)
                        Gw_Server.broadcast(self.log_tmp, self.subscribe_client)
            except:
                pass

class Serial_Monitor:

    def __init__(self):
        self.serial_modify_add()

    async def serial_modify(self):
        context = pyudev.Context()
        monitor = pyudev.Monitor.from_netlink(context)
        monitor.filter_by(subsystem='usb')
        for device in iter(monitor.poll, None):
            await asyncio.sleep(0.2)
            if device.action == 'add':
                self.serial_modify_add()
            if device.action == 'remove':
                self.serial_modify_remove()

    def start(self):
        asyncio.run(self.serial_modify())

    def serial_modify_add(self):
        connect_message = ''
        add = 0
        for files in os.listdir('/dev'):
            if files in Serial_Ctrl_Center.serial_name:
                pass
            else:
                try:
                    re.match('ttyUSB', files).group()
                    path = '/dev/' + files

                    # self.conn_list.append(SerialICM(path))  # 创建连接对象，传参ttyUSBx字符串

                    n = int(files[-1])
                    Serial_Ctrl_Center.serial_list[n] = serial_terminal(n)
                    Serial_Ctrl_Center.serial_name.append(files)
                    Serial_Ctrl_Center.onOpened[n] = True

                    connect_message = connect_message + files + ' '
                    add = add + 1
                except serial.serialutil.SerialException:
                    print(files + '设备异常，请重新连接')
                except OSError:
                    print(files + '打开错误，请重新连接')
                except AttributeError:  # 非USB转串口设备
                    pass
        if add == 0:
            pass
        else:
            print('connected: ' + connect_message + '\n')

    def serial_modify_remove(self):
        done = 1
        for files in Serial_Ctrl_Center.serial_name:
            if files in os.listdir('/dev'):  # 查看连接列表是否在/dev设备列表中
                pass
            else:
                for items in Serial_Ctrl_Center.serial_list:  # 删除断开的连接
                    if items != '':
                        if files == items.conn.port.replace('/dev/', ''):
                            n = int(items.conn.port.replace('/dev/ttyUSB', ''))
                            items.conn.close()
                            print(f'disconnected: ttyUSB{n}\n')
                            Serial_Ctrl_Center.serial_name.remove(files)
                            items = ''
                            done = 0
                        if done:
                            pass
                        else:
                            break


class Serial_Ctrl_Center(object):
    onOpened = [False, False, False, False, False, False, False, False, False, False]
    serial_list = ['', '', '', '', '', '', '', '', '', '']
    serial_name = []


    def __init__(self):
        self.serial_monitor = Serial_Monitor()
        self.serial_monitor_thread = threading.Thread(target=self.serial_monitor.start, daemon=False) # false will not end with main()
        self.serial_monitor_thread.start()

    def keep(self):
        while True:
            pass

class Gw_Server(object):
    def __init__(self):
        # 定义服务器地址和端口
        HOST = 'localhost'
        PORT = 8082

        self.ttyUSBlist = ['ttyUSB0', 'ttyUSB1', 'ttyUSB2', 'ttyUSB3', 'ttyUSB4', 'ttyUSB5', 'ttyUSB6', 'ttyUSB7', 'ttyUSB8', 'ttyUSB9']

        # 创建服务器套接字
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen(5)

    # 广播消息给所有订阅者
    def broadcast(message, clients):
        for client in clients:
            client.send(message.encode())

        # 处理客户端连接
    def handle_client(self, client_socket, addr):
        # 接收客户端的订阅请求
        while True:
            data = client_socket.recv(1024).decode()
            if data in self.ttyUSBlist:
                Serial_Ctrl_Center.serial_list[int(data[-1])].subscribe_client.append(client_socket)
                print(f'Client {addr} subscribed')
            elif data[:11] == 'unsubscribe' and data[11:] in self.ttyUSBlist:
                Serial_Ctrl_Center.serial_list[int(data[-1])].subscribe_client.remove(client_socket)
                print(f'Client {addr} unsubscribed')
            elif data == 'Client closed':
                # clients.remove(client_socket)
                for items in Serial_Ctrl_Center.serial_list:    # del all subscribe
                    if client_socket in items.subscribe_client:
                        items.subscribe_client.remove(client_socket)
                client_socket.close()
                print(f'Client {addr} disconnected')
                break
            else:
                for items in Serial_Ctrl_Center.serial_list:
                    if client_socket in items.subscribe_client:
                        items.conn.write((self.InputA + '\n').encode())

    def start(self):
        # 等待并处理客户端连接
        while True:
            client_socket, addr = self.server_socket.accept()
            print(f'Client {addr} connected')
            thread = threading.Thread(target=self.handle_client, args=(client_socket, addr))
            thread.start()


if __name__ == '__main__':
    serial_ctrl_center = Serial_Ctrl_Center()
    gw_server = Gw_Server()
    gw_server.start()