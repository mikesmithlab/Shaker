from Shaker import arduino
import numpy as np
import time
import matplotlib.pyplot as plt
from Generic import filedialogs


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

    def ramp(self, start, end, rate, step_size=1):
        """Basic Ramp without accelerometer reading"""
        if end > start:
            values = np.arange(start, end + 1, 1*step_size)
        else:
            values = np.arange(start, end - 1, -1*step_size)

        self.init_duty(start, 0.1)
        delay = 1 / rate
        for v in values:
            self.change_duty(v, delay)
        self.init_duty(0)

    def ramp2(self, start, end, rate, readings=1, step_size=1):
        """Ramp with accelerometer readings"""
        if end > start:
            values = np.arange(start, end + 1, 1*step_size)
        else:
            values = np.arange(start, end - 1, -1*step_size)
        self.init_duty(start, 0.1)
        delay = 1 / rate
        string = ''
        for v in values:
            self.change_duty(v)
            for r in range(readings):
                time.sleep(delay/readings)
                self.accel_pointer()
                string += self.ps_ard.read_all()
        self.init_duty(end)
        time.sleep(1)
        string += self.ps_ard.read_all()
        return string, values

    def sample(self, samples, rate):
        delay = 1/rate
        string = ''
        times = []
        t = time.time()
        for s in range(samples):
            time.sleep(delay)
            self.accel_pointer()
            times.append(time.time() - t)
            string += self.ps_ard.read_all()
        time.sleep(1)
        string += self.ps_ard.read_all()
        a = parse_a(string)
        return a, times


    def init_duty(self, val, delay=0.01):
        string = 'i{:03}'.format(val)
        self.ps_ard.send_serial_line(string)
        self.speaker.send_serial_line(string[1:])
        time.sleep(delay)

    def change_duty(self, val, delay=0.01):
        string = 'd{:03}'.format(val)
        self.ps_ard.send_serial_line(string)
        self.speaker.send_serial_line(string[1:])
        time.sleep(delay)

    def read_accel(self, sleep=0.1):
        self.ps_ard.flush()
        self.ps_ard.send_serial_line('a')
        time.sleep(sleep)
        lines = self.ps_ard.readlines(6)
        print(lines)
        a = [float(lines[i][2:7]) for i in (2, 3, 4)]
        return a

    def accel_pointer(self):
        self.ps_ard.send_serial_line('a')

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

    def read_all(self):
        lines, string = self.ps_ard.read_all()
        return lines, string

    def quit(self):
        self.switch_mode()


def parse_a(string):
    list_of_strings = string.split("\r\n")
    a = []
    for l in list_of_strings:
        if 'Accel' in l:
            x, y, z = l.split("\n")[2:5]
            x, y, z = (float(x[2:7]), float(y[2:7]), float(z[2:7]))
            a.append((x, y, z))
    return np.array(a)


def plot_mag_a(string, readings, values, save_data=False, plot=False):
    a = parse_a(string)
    a_mag = np.linalg.norm(a, axis=1)
    a_reshaped = np.reshape(a_mag, (len(values), readings))
    mean_a = np.mean(a_reshaped, axis=1)
    a_err = np.std(a_reshaped, axis=1)/np.sqrt(readings)
    if save_data:
        folder = filedialogs.create_directory()
        print(folder)
        np.savetxt(folder+'/values.txt', values)
        np.savetxt(folder+'/mean.txt', mean_a)
        np.savetxt(folder+'/error.txt', a_err)
    if plot:
        plt.figure()
        plt.errorbar(values, mean_a, yerr=a_err, marker='x')
        plt.xlabel('Duty Cycle (%)')
        plt.ylabel('Acceleration (m/s2)')
        plt.show()
    return values, mean_a, a_err, a_reshaped


def plot_all_a(string, readings, values, save_data=False, plot=False):
    a = parse_a(string)
    a = a.reshape((len(values), readings, 3))
    mean_a = np.mean(a, axis=1)
    std_a = np.std(a, axis=1)
    if plot:
        plt.figure()
        plt.errorbar(values, mean_a[:, 0], yerr=std_a[:, 0], marker='x')
        plt.errorbar(values, mean_a[:, 1], yerr=std_a[:, 1], marker='o')
        plt.errorbar(values, mean_a[:, 2], yerr=std_a[:, 2], marker='+')
        plt.legend(['x', 'y', 'z'])
        plt.xlabel('Duty Cycle (%)')
        plt.ylabel('Acceleration (m/s2)')
        plt.show()
    return values, mean_a, std_a




if __name__ == "__main__":
    PS = PowerSupply()
    readings = 5
    string, values = PS.ramp2(40, 80, 1, readings=readings)
    PS.quit()
    values, mean_a, a_err = plot_mag_a(string, readings, values, plot=True)
    plot_all_a(string, readings, values)