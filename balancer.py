import Shaker.arduino as arduino
import Shaker.stepper as stepper
import Shaker.loadcell as loadcell

class Balancer():
    """
    Class to balance the shaker using stepper motors and loadcells
    """
    def __init__(self, port=None):
        """ Initise the Arduino, Stepper and LoadCell classes """
        self.ard = arduino.Arduino(port)
        self.Stepper = stepper.Stepper(self.ard)
        self.LoadCell = loadcell.LoadCell(self.ard)

    def read_forces(self, cell):
        """ Read the force from a load_cell"""
        force = self.LoadCell.read_force(cell=cell)
        return force

    def move_motor(self, motor, steps, direction):
        """ Move a stepper motor """
        self.Stepper.move_motor(motor, steps, direction)

    def clean_up(self):
        """ link to quit serial """
        self.ard.quit_serial()


if __name__=="__main__":
    bal = Balancer(port='/dev/ttyACM0')
    force = bal.read_forces(3)
    print(force)
    bal.move_motor(1, 100, '-')
    bal.clean_up()
