import numpy as np

duty = np.loadtxt("/home/ppxjd3/Code/Shaker/duties_map.txt")
accel = np.loadtxt("/home/ppxjd3/Code/Shaker/acceleration_map_volts.txt")


def duty_to_accel(d_arr):
    mapping = {d: a for d, a in zip(duty, accel)}
    a = [mapping[d] for d in d_arr]
    return a


if __name__ == "__main__":
    print(duty_to_accel([30, 500, 200]))
