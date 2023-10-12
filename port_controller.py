# rebuild the code struct
import asyncio
import serial_terminal
# readline.parse_and_bind("tab: complete")
# readline.parse_and_bind("set editing-mode vi")


# 文件追加写入
def save_to_file(file_name, contents):
    fh = open(file_name, 'a')
    fh.write(contents)
    fh.close()


# 文件内容清空
def clear_file(file_name):
    fh = open(file_name, 'w').close()


class port_controller(object):
    
    def __init__(self):
        # self.conn = []
        pass

    def port_terminal(self):            # index select session
        ch = 1
        while ch:
            InputB = input('choose port( 0 ~ 9 | quit | h)->')
            if(InputB == 'quit') or (InputB == 'QUIT'):
                print('INFO: Serial Controller closed!')
                # del serial_terminal
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
                        conn = serial_terminal.serial_terminal(i)
                        asyncio.run(conn.serial_terminal())
                        del conn
                        ch = 0
                        break
                
        # asyncio.run(self.serial_terminal())

    def port_controller(self):
        while 1:
            self.port_terminal()

    def help(self):
        print('|---------------------------------------------------------|')
        print('|----------------------#help -v2.0.0----------------------|')
        print('|                                                         |')
        print('| input 0 ~ 9 to choose ttyUSB0~9                         |')
        print('| input quit to quit the program                          |')
        print('|                                                         |')
        print('| when using serial:                                      |')
        print('| input q will return to choosing port                    |')
        print('| input echo on/off to enable/disable the echo            |')
        print('|                                                         |')
        print('|                                                         |')
        print('|---------------------------------------------------------|')


if __name__ == '__main__':
    try:
        port_controller = port_controller()
        # filename = ['/home/pi/.remote_env/log/MCU_' + time.strftime('%Y-%m-%d-%H_%M_%S', time.localtime()) + '.log',
        #             '/home/pi/.remote_env/log/SOC_' + time.strftime('%Y-%m-%d-%H_%M_%S', time.localtime()) + '.log']
        port_controller.port_controller()
    except KeyboardInterrupt:
        # readline.clear_history()
        print('\nINFO: Serial Controller closed!')
