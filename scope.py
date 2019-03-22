import time
from picoscope import ps2000
import numpy as np
import time

class Scope:

    def __init__(self):
        self.ps = ps2000.PS2000()
        waveform_desired_duration = 100E-3
        obs_duration = 3 * waveform_desired_duration
        sampling_interval = obs_duration / 4096
        (self.actualSamplingInterval, self.nSamples, maxSamples) = \
            self.ps.setSamplingInterval(sampling_interval, obs_duration)
        channelRange = self.ps.setChannel('A', 'DC', 2.0, 0.0, enabled=True,
                                     BWLimited=False)
        self.ps.setSimpleTrigger('A', 1.0, 'Falling', timeout_ms=100, enabled=True)


    def get_V(self):
        s = time.time()
        self.ps.runBlock()
        self.ps.waitReady()
        data = self.ps.getDataV('A', self.nSamples, returnOverflow=False)
        times = np.arange(self.nSamples)*self.actualSamplingInterval
        return times, data, time.time() - s

if __name__=="__main__":
    S = Scope()
    t, V, l = S.get_V()
    print(l)
    import matplotlib.pyplot as plt
    plt.figure()
    plt.plot(t, V)
    plt.show()
    t, V, l = S.get_V()
    plt.figure()
    plt.plot(t, V)
    plt.show()