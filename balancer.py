import Shaker.arduino as arduino
import Shaker.stepper as stepper
import Shaker.loadcell as loadcell
import Generic.camera as camera
import Generic.images as images
import numpy as np
import time
import cv2
from scipy import ndimage
import scipy.spatial as ss


class Balancer():
    """
    Class to balance the shaker using stepper motors and loadcells
    """
    def __init__(self, port=None, no_of_sides=None):
        """ Initise the Arduino, Stepper and LoadCell classes """
        cam_num = camera.find_camera_number()
        if port == None:
            port = arduino.find_port()
        if no_of_sides == None:
            self.no_of_sides = int(input('Enter the number of sides: '))
        else:
            self.no_of_sides = no_of_sides
        self.ard = arduino.Arduino('/dev/'+port)
        self.Stepper = stepper.Stepper(self.ard)
        self.LoadCell = loadcell.LoadCell(self.ard)
        self.webcam = camera.Camera(cam_type='philips 3', cam_num=cam_num)
        self.crop_first_frame()

    def view_center(self):
        loopvar = True
        while loopvar:
            frame = self.get_frame()
            frame, centroid = self.mark_center(frame)
            self.find_instruction(centroid)
            cv2.imshow('center', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                loopvar=False

    def find_instruction(self, centroid):
        centroid = np.array(centroid).reshape(1, 2)
        dist = ss.distance.cdist(centroid, self.corners)
        closest = np.argmin(dist)
        instructions = {0: 'raise 1', 1: 'raise 1 and 2', 2: 'raise 2',
                        3: 'lower 1', 4: 'lower 1 and 2', 5: 'lower 2'}
        print(instructions[closest])

    @staticmethod
    def find_corners(points):
        if len(np.shape(points)) == 1:
            cx, cy, r = points
            sin30 = 0.5
            cos30 = np.sqrt(3)/2
            corners = np.array([[cx, cy-r],
                                [cx+r*cos30, cy-r*sin30],
                                [cx+r*cos30, cy+r*sin30],
                                [cx, cy+r],
                                [cx-r*cos30, cy+r*sin30],
                                [cx-r*cos30, cy-r*sin30]])
        else:
            corners = points

        return corners

    def mark_center(self, frame):
        centroid = self.find_centroid(frame)
        frame = images.draw_circle(frame, centroid[0], centroid[1], 5,
                                   color=images.RED)
        frame = images.draw_circle(frame, self.xc, self.yc, 3,
                                   color=images.PINK)
        return frame, centroid

    def get_frame(self):
        frame = self.webcam.single_pic_array()
        frame = images.crop_and_mask_image(frame, self.crop, self.mask,
                                           'white')
        return frame

    def crop_first_frame(self):
        frame = self.webcam.single_pic_array()
        crop_inst = images.CropShape(frame, self.no_of_sides)
        self.mask, self.crop, points = crop_inst.begin_crop()
        if len(np.shape(points)) > 1:
            self.xc = np.mean(points[:, 0])
            self.yc = np.mean(points[:, 1])
        else:
            self.xc = points[0]
            self.yc = points[1]
        self.xc -= self.crop[1, 0]
        self.yc -= self.crop[0, 0]
        self.corners = self.find_corners(points)
        self.corners[:, 0] -= self.crop[1, 0]
        self.corners[:, 1] -= self.crop[0, 0]
        first_frame = images.crop_and_mask_image(frame, self.crop, self.mask,
                                                 mask_color='white')
        images.display(first_frame, 'first')

    def read_forces(self, cell):
        """ Read the force from a load_cell"""
        force = self.LoadCell.read_force(cell=cell)
        return force

    @staticmethod
    def find_centroid(img):
        img = images.bgr_2_grayscale(~img)
        center = ndimage.measurements.center_of_mass(img)
        return center[1], center[0]

    def move_motor(self, motor, steps, direction):
        """ Move a stepper motor """
        self.Stepper.move_motor(motor, steps, direction)

    def clean_up(self):
        """ link to quit serial """
        self.ard.quit_serial()
        self.webcam.close()


if __name__=="__main__":
    bal = Balancer()
    #force = bal.read_forces(3)
    #print(force)
    #bal.move_motor(1, 100, '-')
    bal.view_center()
    bal.clean_up()
