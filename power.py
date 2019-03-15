from Shaker import arduino
import numpy as np
import time

SPEAKER = "/dev/serial/by-id/usb-Arduino_LLC_Arduino_Micro-if00"
POWERSUPPLY = "/dev/serial/by-id/usb-Arduino__www.arduino.cc__0043_757353034313511092C1-if00"


class PowerSupply:

    def __init__(self):
        self.ps_ard = arduino.Arduino(port=POWERSUPPLY, rate=115200, wait=False)
        self.ps_ard.flush()
        self.speaker = arduino.Arduino(port=SPEAKER, rate=115200, wait=False)
        self.start_serial()

    def start_serial(self):
        message = self.switch_mode()
        if message == 'Serial control enabled.\r\n':
            print(message)
        elif message == 'Manual control enabled.\r\n':
            print('Send command again')
            message = self.switch_mode()
            print(message)
        else:
            print('Something wrong')
            print(message)

    def switch_mode(self):
        self.ps_ard.send_serial_line('x')
        time.sleep(0.01)
        lines = self.ps_ard.readlines(2)
        message = lines[1]
        return message

    def ramp(self, start, end, rate, read=False):

        if end > start:
            values = np.arange(start, end + 1, 1)
        else:
            values = np.arange(start, end - 1, -1)

        self.init_duty(start, 0.1)
        delay = 1 / rate
        a = []
        g = []
        m = []
        t = time.time()
        for v in values:
            self.change_duty(v, delay/4)
            a.append(self.read_accel(delay/4))
            g.append(self.read_gyro(delay/4))
            m.append(self.read_mag(delay/4))
        self.init_duty(0)
        print(time.time() - t)
        print(len(values) * delay)
        print(a)
        if read:
            return a, g, m

    def init_duty(self, val, delay=0.01):
        string = 'i{:03}'.format(val)
        self.ps_ard.send_serial_line(string)
        self.speaker.send_serial_line(string[1:])
        time.sleep(delay)
        self.ps_ard.ignorelines(4)

    def change_duty(self, val, delay=0.01):
        string = 'd{:03}'.format(val)
        self.ps_ard.send_serial_line(string)
        self.speaker.send_serial_line(string[1:])
        time.sleep(delay)
        lines = self.ps_ard.readlines(4)

    def read_accel(self, sleep=0.1):
        self.ps_ard.flush()
        self.ps_ard.send_serial_line('a')
        time.sleep(sleep)
        lines = self.ps_ard.readlines(6)
        a = [float(lines[i][2:7]) for i in (2, 3, 4)]
        return a

    def read_gyro(self, sleep=0.1):
        self.ps_ard.flush()
        self.ps_ard.send_serial_line('g')
        time.sleep(sleep)
        lines = self.ps_ard.readlines(6)
        g = [float(lines[i][2:7]) for i in (2, 3, 4)]
        return g

    def read_mag(self, sleep=0.1):
        self.ps_ard.flush()
        self.ps_ard.send_serial_line('m')
        time.sleep(sleep)
        lines = self.ps_ard.readlines(6)
        m = [float(lines[i][2:7]) for i in (2, 3, 4)]
        return m


if __name__ == "__main__":
    PS = PowerSupply()
    # g = PS.read_gyro()
    # t = time.time()
    # a = PS.read_accel()
    # PS.read_gyro()
    # PS.read_mag()
    a, g, m = PS.ramp(0, 40, 3, read=True)
    # s = time.time()
    # PS.init_duty(0)
    # time.sleep(3)
    # PS.change_duty(100)
    # time.sleep(3)
    # PS.change_duty(0)
    # time.sleep(3)
    # PS.init_duty(0)
    # print(time.time() - s)
    # PS.start_serial()
