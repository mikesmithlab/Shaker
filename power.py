import time

import numpy as np

from Generic.equipment import arduino

SPEAKER = "/dev/serial/by-id/usb-Arduino_LLC_Arduino_Micro-if00"
POWERSUPPLY = "/dev/serial/by-id/usb-Arduino__www.arduino.cc__0043_757353034313511092C1-if00"


class PowerSupply:

    def __init__(self, tone=True):
        self.ps_ard = arduino.Arduino(port=POWERSUPPLY, rate=115200, wait=False)
        self.ps_ard.flush()
        self.tone = tone
        if self.tone:
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
            self.start_serial()

    def switch_mode(self):
        self.ps_ard.send_serial_line('x')
        time.sleep(0.1)
        lines = self.ps_ard.readlines(2)
        message = lines[1]
        return message

    def ramp(self, start, end, rate, step_size=1, record=True,
             stop_at_end=True):
        """Basic Ramp without accelerometer reading"""
        if end > start:
            values = np.arange(start, end + 1, 1*step_size)
        else:
            values = np.arange(start, end - 1, -1*step_size)
        self.init_duty(start) if record else self.change_duty(start)
        delay = 1 / rate
        time.sleep(delay)
        for v in values:
            t = time.time()
            self.change_duty(v)
            interval = delay - (time.time() - t)
            if interval > 0:
                time.sleep(delay - (time.time() - t))
        if stop_at_end:
            self.init_duty(0) if record else self.change_duty(0)
        else:
            self.init_duty(end) if record else self.change_duty(end)

    def ramp_up_and_down(self, start, end, rate, step_size):
        if end > start:
            values = np.arange(start, end + 1, 1*step_size)
            next_values = np.arange(end, start-1, -1*step_size)
            values = np.append(values, next_values)
        else:
            values = np.arange(start, end - 1, -1*step_size)
            next_values = np.arange(start, end + 1, 1*step_size)
            values = np.append(values, next_values)

        self.init_duty(start)
        delay = 1/rate
        time.sleep(delay)
        for v in values:
            t = time.time()
            self.change_duty(v)
            interval = delay - time.time() + t
            if interval > 0:
                time.sleep(interval)
        self.init_duty(0)

    def init_duty(self, val):
        string = 'i{:03}'.format(val)
        self.ps_ard.send_serial_line(string)
        if self.tone:
            self.speaker.send_serial_line(string[1:])
        _ = self.read_all()

    def change_duty(self, val):
        string = 'd{:03}'.format(val)
        self.ps_ard.send_serial_line(string)
        if self.tone:
            self.speaker.send_serial_line(string[1:])
        _ = self.read_all()


    def read_all(self):
        string = self.ps_ard.read_all()
        return string

    def quit(self):
        self.switch_mode()


if __name__ == "__main__":
    PS = PowerSupply()
    PS.ramp(40, 80, 1)
    PS.quit()
