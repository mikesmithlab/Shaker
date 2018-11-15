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
        self.webcam = camera.Camera(cam_type='logitechHD1080p', cam_num=cam_num)
        self.mask, self.crop, self.points = self.crop_first_frame()
        self.corners = self.find_corners()
        self.xc, self.yc = self.find_tray_center()
        self.level = False

    def crop_first_frame(self):
        """Finds the mask, crop and selection points for first frame"""
        frame = self.webcam.single_pic_array()
        crop_inst = images.CropShape(frame, self.no_of_sides)
        mask, crop, points = crop_inst.begin_crop()
        return mask, crop, points

    def find_corners(self):
        """Finds the 6 corners of the hexagonal base"""
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
            corners = self.points.copy()
        corners[:, 0] -= self.crop[0, 0]
        corners[:, 1] -= self.crop[0, 1]
        return corners

    def find_tray_center(self):
        """Finds the center of the tray using the crop points"""
        if len(np.shape(self.points)) > 1:
            xc = np.mean(self.points[:, 0])
            yc = np.mean(self.points[:, 1])
            print("check")
        else:
            xc = self.points[0]
            yc = self.points[1]
            # self.crop = ([xmin, ymin], [xmax, ymax])
        xc -= self.crop[0, 0] # -= xmin
        yc -= self.crop[0, 1] # -= ymin
        return xc, yc

    def view_center(self):
        """Shows live web cam view with the center marked"""
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
        """Performs the levelling of the tray"""
        start_time = time.time()
        while self.level == False:
            time.sleep(interval_time)
            frame = self.time_average_center()
            end_time = time.time()-start_time
            if end_time > fail_time:
                print('Levelling time out')
                break
        cv2.destroyAllWindows()

    def time_average_center(self, num=10, delay=0.5, show=False):
        """Finds the center of the particles over time"""
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
        self.find_instruction(centroid, complete=True)
        return frame

    def get_frame(self):
        """Gets the current frame from the webcam"""
        frame = self.webcam.single_pic_array()
        frame = images.crop_and_mask_image(frame, self.crop, self.mask,
                                           'white')
        return frame

    @staticmethod
    def find_particle_center(img):
        """Finds the center of mass of the particles"""
        img = images.bgr_2_grayscale(255-img)
        img = images.threshold(img, 150, cv2.THRESH_TOZERO)
        center = ndimage.measurements.center_of_mass(img)
        return center[1], center[0]

    def mark_centers(self, frame, centroid):
        """ Draws the object center in red and actual center in pink"""
        frame = images.draw_circle(frame, centroid[0], centroid[1], 5,
                                   color=images.RED)
        print(self.xc, self.yc)
        frame = images.draw_circle(frame, self.xc, self.yc, 3,
                                   color=images.PINK)
        return frame

    def find_instruction(self, centroid, complete=False):
        centroid = np.array(centroid).reshape(1, 2)
        dist = ss.distance.cdist(centroid, self.corners)
        closest_corner = np.argmin(dist)
        instructions = {0: 'raise motor 2',
                        1: 'raise motors 1 and 2',
                        2: 'raise motor 1',
                        3: 'lower motor 2',
                        4: 'lower motors 1 and 2',
                        5: 'lower motor 1'}
        dist_to_center = np.sqrt((self.yc-centroid[0, 0])**2 +
                                 (self.yc-centroid[0, 1])**2)
        if dist_to_center > 15:
            print(instructions[closest_corner])
            if complete:
                self.run_instruction(instructions[closest_corner])
        else:
            print('flat enough')
            self.level = True

    def run_instruction(self, instruction):
        if instruction == 'raise motor 1':
            self.move_motor(1, 100, '+')
        elif instruction == 'lower motor 1':
            self.move_motor(1, 100, '-')
        elif instruction == 'raise motor 2':
            self.move_motor(2, 100, '+')
        elif instruction == 'lower motor 2':
            self.move_motor(2, 100, '-')
        elif instruction == 'raise motors 1 and 2':
            self.move_motor(1, 100, '+')
            self.move_motor(2, 100, '+')
        elif instruction == 'lower motors 1 and 2':
            self.move_motor(1, 100, '-')
            self.move_motor(2, 100, '-')

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
    bal.view_center()
    #bal.level_tray()
    bal.clean_up()
