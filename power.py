from Shaker import arduino
import numpy as np
import time

SPEAKER = "/dev/serial/by-id/usb-Arduino_LLC_Arduino_Micro-if00"
POWERSUPPLY = "/dev/serial/by-id/usb-Arduino__www.arduino.cc__0043_757353034313511092C1-if00"


class PowerSupply:

    def __init__(self):
        self.ps_ard = arduino.Arduino(port=POWERSUPPLY, rate=115200, wait=False)
        self.speaker = arduino.Arduino(port=SPEAKER, rate=115200, wait=False)
        self.start_serial()

    def start_serial(self):
        self.ps_ard.send_serial_line('t')
        time.sleep(0.1)
        self.ps_ard.send_serial_line('x')

    def camera_trigger(self):
        self.ps_ard.send_serial_line('')  # Need to find out command

    def ramp(self, start, end, rate):

        if end > start:
            values = np.arange(start + 1, end + 1, 1)
        else:
            values = np.arange(start - 1, end - 1, -1)

        self.init_duty(start)
        delay = 1 / rate
        for v in values:
            time.sleep(delay)
            self.change_duty(v)
        print(len(values) * delay)
        self.init_duty(0)

    def init_duty(self, val):
        string = 'i{:03}'.format(val)
        self.ps_ard.send_serial_line(string)
        self.speaker.send_serial_line(string[1:])

    def change_duty(self, val):
        string = 'd{:03}'.format(val)
        self.ps_ard.send_serial_line(string)
        self.speaker.send_serial_line(string[1:])



if __name__ == "__main__":
    PS = PowerSupply()
    PS.ramp(0, 40, 1)
    s = time.time()
    # PS.init_duty(0)
    # time.sleep(3)
    # PS.change_duty(100)
    # time.sleep(3)
    # PS.change_duty(0)
    # time.sleep(3)
    # PS.init_duty(0)
    # print(time.time() - s)
    # PS.start_serial()
