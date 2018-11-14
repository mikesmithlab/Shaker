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
        self.mask, self.crop, self.points = self.crop_first_frame()
        self.corners = self.find_corners()
        self.xc, self.yc = self.find_tray_center()
        self.level = False

    def crop_first_frame(self):
        frame = self.webcam.single_pic_array()
        crop_inst = images.CropShape(frame, self.no_of_sides)
        mask, crop, points = crop_inst.begin_crop()
        frame = images.crop_and_mask_image(frame, crop, mask, 'white')
        images.display(frame)
        return mask, crop, points

    def find_corners(self):
        if len(np.shape(self.points)) == 1:
            cx, cy, r = self.points
            sin30 = 0.5
            cos30 = np.sqrt(3)/2
            corners = np.array([[cx, cy-r],
                                [cx+r*cos30, cy-r*sin30],
                                [cx+r*cos30, cy+r*sin30],
                                [cx, cy+r],
                                [cx-r*cos30, cy+r*sin30],
                                [cx-r*cos30, cy-r*sin30]])
        else:
            corners = self.points
        corners[:, 0] -= self.crop[1, 0]
        corners[:, 1] -= self.crop[0, 0]
        return corners

    def find_tray_center(self):
        if len(np.shape(self.points)) > 1:
            xc = np.mean(self.points[:, 0])
            yc = np.mean(self.points[:, 1])
        else:
            xc = self.points[0]
            yc = self.points[1]
        xc -= self.crop[1, 0]
        yc -= self.crop[0, 0]
        return xc, yc

    def view_center(self):
        loopvar = True
        while loopvar:
            frame = self.get_frame()
            centroid = self.find_particle_center(frame)
            frame = self.mark_centers(frame, centroid)
            self.find_instruction(centroid)
            cv2.imshow('center', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                loopvar=False

    def level_tray(self, interval_time=10, fail_time=30):
        start_time = time.time()
        while self.level == False:
            time.sleep(interval_time)
            self.time_average_center()
            end_time = time.time()-start_time
            if end_time > fail_time:
                print('Levelling time out')
                break

    def time_average_center(self, num=10, delay=0.5, show=False):
        cx = []
        cy = []
        for r in range(num):
            time.sleep(delay)
            frame = self.get_frame()
            centroid = self.find_particle_center(frame)
            cx.append(centroid[0])
            cy.append(centroid[1])
        centroid = (np.mean(cx), np.mean(cy))
        frame = self.mark_centers(frame, centroid)
        self.find_instruction(centroid)
        if show:
            images.display(frame, 'time average center')

    def get_frame(self):
        frame = self.webcam.single_pic_array()
        frame = images.crop_and_mask_image(frame, self.crop, self.mask,
                                           'white')
        return frame

    @staticmethod
    def find_particle_center(img):
        img = images.bgr_2_grayscale(255-img)
        center = ndimage.measurements.center_of_mass(img)
        return center[1], center[0]

    def mark_centers(self, frame, centroid):
        frame = images.draw_circle(frame, centroid[0], centroid[1], 5,
                                   color=images.RED)
        frame = images.draw_circle(frame, self.xc, self.yc, 3,
                                   color=images.PINK)
        return frame

    def find_instruction(self, centroid):
        centroid = np.array(centroid).reshape(1, 2)
        dist = ss.distance.cdist(centroid, self.corners)
        closest_corner = np.argmin(dist)
        instructions = {0: 'raise 1', 1: 'raise 1 and 2', 2: 'raise 2',
                        3: 'lower 1', 4: 'lower 1 and 2', 5: 'lower 2'}
        dist_to_center = np.sqrt((self.yc-centroid[0, 0])**2 +
                                 (self.yc-centroid[0, 1])**2)
        if dist_to_center > 15:
            print(instructions[closest_corner])
        else:
            print('flat enough')
            self.level = True

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
        self.webcam.close()


if __name__=="__main__":
    bal = Balancer()
    #force = bal.read_forces(3)
    #print(force)
    #bal.move_motor(1, 100, '-')
    #bal.view_center()
    bal.level_tray()
    bal.clean_up()
