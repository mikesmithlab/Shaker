import numpy as np

duties = np.loadtxt("/home/ppxjd3/Code/Shaker/duties_map.txt")
accels = np.loadtxt("/home/ppxjd3/Code/Shaker/acceleration_map_volts.txt")


def get_ramp(start, end, steps):
    if (start < accels.min()) or (start > accels.max()):
        print("start out of bounds")
        return 0
    if (end < accels.min()) or (end > accels.max()):
        print("end out of bounds")
        return 0
    accel_values = np.linspace(start, end, steps)
    accel_args = [np.abs((accels - v)).argmin() for v in accel_values]
    return duties[accel_args]
