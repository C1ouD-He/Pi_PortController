import os
import re
import asyncio
import threading
import serial
import pyudev
import socket

log_listener = []
def server_log(log):
    print(log)
    Port_Server.broadcast(log, log_listener)

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

class serial_terminal(object):
    def __init__(self,n):
        self.n = n
        self.input_tmp = ''
        self.last_cmd = ''
        self.status = True
        self.subscribe_client = []
        try:
            self.conn = serial.Serial(f'/dev/ttyUSB{self.n}', baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=0.5)
            self.start_log_reading()
        except serial.serialutil.SerialException:
            server_log(f'ERROR: ttyUSB{self.n} undetected!')
            self.status = False

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
                log_tmp = self.conn.read(1).decode()#.strip()
                self.conn.flushOutput()
                Port_Server.broadcast(log_tmp, self.subscribe_client)
            except Exception:
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
                    # 创建连接对象，传参ttyUSBx字符串
                    n = int(files[-1])
                    Serial_Ctrl_Center.serial_list[n] = serial_terminal(n)
                    Serial_Ctrl_Center.serial_name.append(files)
                    Serial_Ctrl_Center.onOpened[n] = True
                    connect_message = connect_message + files + ' '
                    add = add + 1
                except serial.serialutil.SerialException:
                    server_log(files + '设备异常，请重新连接')
                except OSError:
                    server_log(files + '打开错误，请重新连接')
                except AttributeError:  # 非USB转串口设备
                    pass
        if add == 0:
            pass
        else:
            server_log('connected: ' + connect_message + '\n')

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
                            server_log(f'disconnected: ttyUSB{n}\n')
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
        self.serial_monitor_thread = threading.Thread(target=self.serial_monitor.start, daemon=True) # false will not end with main()
        self.serial_monitor_thread.start()

    def keep(self):
        while True:
            pass

class Port_Server(object):
    def __init__(self):
        # 定义服务器地址和端口
        # HOST = 'localhost'
        HOST = get_local_ip()
        PORT = 8082

        self.ttyUSBlist = ['ttyUSB0', 'ttyUSB1', 'ttyUSB2', 'ttyUSB3', 'ttyUSB4', 'ttyUSB5', 'ttyUSB6', 'ttyUSB7', 'ttyUSB8', 'ttyUSB9']

        # 创建服务器套接字
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen(5)


    # 广播消息给所有订阅者
    def broadcast(message, clients):
        for client in clients:
            try:
                client.send(message.encode())
            except BrokenPipeError:
                client.close()

        # 处理客户端连接
    def handle_client(self, client_socket, addr):
        # 接收客户端的订阅请求
        while True:
            try:
                data = client_socket.recv(128).decode()
            except OSError:
                # server_log(f'{e}')
                self.onDisconnect(client_socket, addr)
                break
            if data == '':
                self.onDisconnect(client_socket, addr)
                break
            elif data in self.ttyUSBlist:
                Serial_Ctrl_Center.serial_list[int(data[-1])].subscribe_client.append(client_socket)
                server_log(f'Client {addr} subscribed {data}')
            elif data[:11] == 'unsubscribe' and data[11:] in self.ttyUSBlist:
                Serial_Ctrl_Center.serial_list[int(data[-1])].subscribe_client.remove(client_socket)
                server_log(f'Client {addr} unsubscribed {data[11:]}')
            elif data == 'svrlog':
                log_listener.append(client_socket)
                server_log(f'Client {addr} subscribed server log')
            elif data == 'unsubscribesvrlog':
                log_listener.remove(client_socket)
                server_log(f'Client {addr} unsubscribed server log')
            elif data == 'Client closed':
                self.onDisconnect(client_socket, addr)
                break
            else:
                for items in Serial_Ctrl_Center.serial_list:
                    if items =='':
                        pass
                    elif client_socket in items.subscribe_client:
                        items.conn.write(data.encode())   # + '\n').encode())
                        if data != '\n':
                            server_log(f'Client {addr} send to ttyUSB{items.n}: {data}')
        del client_socket

    def onDisconnect(self, client_socket, addr):
        for items in Serial_Ctrl_Center.serial_list:    # del all subscribe
            if items =='':
                pass
            elif client_socket in items.subscribe_client:
                items.subscribe_client.remove(client_socket)
        client_socket.close()
        server_log(f'Client {addr} disconnected')

    def start(self):
        try:
            # 等待并处理客户端连接
            while True:
                client_socket, addr = self.server_socket.accept()
                server_log(f'Client {addr} connected')
                thread = threading.Thread(target=self.handle_client, args=(client_socket, addr), daemon=True)
                thread.start()
        except KeyboardInterrupt:
            server_log('GW_Server closed!')
            self.server_socket.close()


if __name__ == '__main__':
    serial_ctrl_center = Serial_Ctrl_Center()
    port_server = Port_Server()
    port_server.start()
