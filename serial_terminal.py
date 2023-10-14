import os
import serial
import asyncio
import threading

class serial_conn(object):
    def __init__(self,n):
        pass

class serial_terminal(object):
    def __init__(self,n):
        import readline
        self.readline = readline
        self.input_tmp = ''
        self.echo = False
        self.mcu_project = ''
        self.soc_commond = False
        self.last_cmd = ''
        self.InputA = ''
        self.ser = []
        self.log_tmp = ''
        self.status = True
        try:
            self.ser = serial.Serial(f'/dev/ttyUSB{n}', baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=0.5)
            self.start_log_reading()
        except serial.serialutil.SerialException:
            print(f'ERROR: ttyUSB{n} undetected!')
            self.status = False

        self.histfile = '/home/pi/.remote_env/Pi_PortController/.port_history'
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
            self.ser.open()
        except serial.serialutil.SerialException:
            pass
        self.onOpened = True
        tlog = threading.Thread(target=self.log_reading, daemon=True)  # 开启log监听线程
        tlog.start()

    # log监听线程
    def log_reading(self):
        while self.onOpened:
            try:
                self.log_tmp = self.ser.readline().decode().strip()
                self.ser.flushOutput()
                if self.log_tmp != '' and (self.log_tmp != (self.input_tmp) or self.echo):   # echo control
                    if(self.log_tmp == '#'):
                        self.soc_commond = True
                    elif 'MCU:' in self.log_tmp:
                        self.soc_commond = False
                        self.mcu_project = self.log_tmp
                    else:
                        print(self.log_tmp)
            except:
                pass

    async def serial_terminal(self):        # serial terminal
        self.readline.clear_history()
        self.readline.read_history_file(self.histfile)
        if self.status == True:
            self.ser.write(chr(0x0D).encode())
            await asyncio.sleep(0.7)
        while 1:
            if self.status == False:
                self.InputA = 'q'
            else:
                try:
                    if(self.soc_commond == False):
                        self.InputA = input(self.mcu_project)
                    else:
                        # await asyncio.sleep(0.1)            # print the '#' below the output if SOC
                        self.InputA = input('# ')
                except KeyboardInterrupt:
                    self.ser.write(chr(0x03).encode())
                    print('')
                    continue
                    #await asyncio.sleep(0.5)

            if(self.InputA == 'q') or (self.InputA == 'Q'):
                self.onOpened = False
                self.echo = False
                try:
                    self.ser.close()
                    print('INFO: Closed serial!')
                except:
                    pass
                self.clear_terminal()
                return
            elif(self.InputA == 'echo on'):
                if(self.echo == False):
                    print('INFO: echo on!')
                self.echo = True
            elif(self.InputA == 'echo off'):
                if(self.echo == True):
                    print('INFO: echo off!')
                self.echo = False
            else:
                self.ser.write((self.InputA + '\n').encode())
                self.input_tmp = self.InputA
                self.InputA = ''
                # await asyncio.sleep(0.03)
