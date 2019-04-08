import time
from picoscope import ps2000
import numpy as np
import time
import matplotlib.pyplot as plt

class Scope:

    def __init__(self):
        self.ps = ps2000.PS2000()
        print(self.ps.getAllUnitInfo())
        waveform_desired_duration = 200E-3
        obs_duration = 3 * waveform_desired_duration
        sampling_interval = obs_duration / 4096
        (self.actualSamplingInterval, self.nSamples, maxSamples) = \
            self.ps.setSamplingInterval(sampling_interval, obs_duration)
        channelRange = self.ps.setChannel('A', 'AC', 2.0, 0.0, enabled=True,
                                     BWLimited=False)
        self.ps.setSimpleTrigger('A', 0, 'Falling', timeout_ms=100,
                                 enabled=True)


    def get_V(self, refine_range=False):
        s = time.time()
        if refine_range:
            channelRange = self.ps.setChannel('A', 'AC', 2.0, 0.0,
                                              enabled=True, BWLimited=False)
            self.ps.runBlock()
            self.ps.waitReady()
            data = self.ps.getDataV('A', self.nSamples, returnOverflow=False)
            vrange = np.max(data)
            channelRange = self.ps.setChannel('A', 'AC', vrange, 0.0,
                                              enabled=True, BWLimited=False)
        self.ps.runBlock()
        self.ps.waitReady()
        data = self.ps.getDataV('A', self.nSamples, returnOverflow=False)
        times = np.arange(self.nSamples)*self.actualSamplingInterval
        return times, data, time.time() - s






if __name__=="__main__":
    S = Scope()
    t, V, l = S.get_V(refine_range=True)
    print(l)
    import matplotlib.pyplot as plt
    plt.figure()
    plt.plot(t, V, 'x')
    plt.show()
    t, V, l = S.get_V(refine_range=True)
    plt.figure()
    plt.plot(t, V)
    plt.show()
    # S = Scope()