# -*- coding: utf-8 -*-
"""
Created on Wed Oct 3 10:11:00 2018

@author: ppzjd3
"""

import sys
import serial
import time
import arduino

class LoadCell():
    """
    This is a class to manage reading the values
    from load cells
    """
    def __init__(self, ard):
        """
        Initialise with an instance of arduino.Arduino
        """
        self.ard = ard

    def read_force(self, cell=None):
        """
        Read the force from the load cell and print the results.
        """
        if cell in [1, 2, 3]:
            command = 'r' + str(cell)
            self.ard.send_serial_line(command)
            force = self.ard.read_serial_line()
        else:
            raise Exception("cell should be an integer of either 1, 2 or 3")
        return force

if __name__=="__main__":
    ard = arduino.Arduino()
    lc = LoadCell(ard)
    lc.read_force()
    ard.quit_serial()
