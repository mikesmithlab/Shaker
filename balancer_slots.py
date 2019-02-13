import Shaker.stepper as stepper
import Shaker.arduino as arduino
import Shaker.find_slots as find_slots
import Generic.camera as camera
import Generic.images as images
import numpy as np
from scipy import ndimage
from scipy import spatial as sp
import cv2
import time
import matplotlib.pyplot as plt

class Balancer:
    """
    Class to balance the shaker using stepper motors and the slots
    """

    def __init__(self, port=None, no_of_sides=None, step_size=50):
        cam_num = camera.find_camera_number()
        if port is None:
            port = arduino.find_port()
        if no_of_sides is None:
            self.no_of_sides = int(input('Enter the number of sides'))
        else:
            self.no_of_sides = no_of_sides

        self.ard = arduino.Arduino('/dev/'+port)
        self.Stepper = stepper.Stepper(self.ard)
        self.webcam = camera.Camera(cam_type='logitechHD1080p', cam_num=cam_num)
        self.hex, self.center, self.contours, im = find_slots.find_regions(self.webcam.single_pic_array())
        self.mask, self.masks = self.create_masks()
        self.step_size = step_size

    def create_masks(self):
        im = self.webcam.single_pic_array()
        mask = np.zeros(np.shape(im)[:2])
        masks = []
        for contour in self.contours:
            single_mask = np.zeros(np.shape(im)[:2])
            cv2.fillPoly(mask, [contour],  1)
            cv2.fillPoly(single_mask, [contour], 1)
            masks.append(single_mask)
        return mask.astype(np.uint8), np.array(masks).astype(np.uint8)

    def balance(self, repeats=100, delay=5):
        balanced = False
        instruction = ''
        self.distance = 0
        self.distance_err = 0
        cv2.namedWindow('Levelling', cv2.WINDOW_KEEPRATIO)
        cv2.resizeWindow('Levelling', 1280, 720)
        while balanced is False:
            centers = []
            for f in range(repeats):
                im = self.webcam.single_pic_array()
                center, im = self.find_center(im)
                centers.append(center)
                im = self.annotate_frame(im, center, instruction, f+1, repeats)
                cv2.imshow('Levelling', im)
                if cv2.waitKey(100) & 0xFF == ord('q'):
                    balanced = True
                    print('Balancing Quit')
                    break
            if balanced is False:
                center = np.mean(centers, axis=0)
                distances = sp.distance.cdist(centers, np.reshape(self.center, (1, 2)))
                self.distance = np.mean(distances)
                self.distance_err = np.std(distances)
                instruction = self.find_instruction(center)

                if self.distance > 2:
                    self.run_instruction(instruction)
                    self.delay_view(delay, instruction)
                elif (self.distance <= 2) and (self.distance_err > 0.3):
                    self.delay_view(delay, 'Do Nothing')
                else:
                    print('Balanced')
                    balanced = True

    def delay_view(self, delay, instruction):
        for t in range(2*delay):
            s = time.time()
            im = self.webcam.single_pic_array()
            center, im = self.find_center(im)
            im = self.annotate_frame(im, center, instruction, 'Delay', delay - t/2)
            cv2.imshow('Levelling', im)
            cv2.waitKey(1)
            interval = time.time() - s
            if interval < 0.5:
                time.sleep(0.5 - interval)


    def run_instruction(self, inst):
        val = self.step_size
        if inst == 'Lower Motors 1 and 2':
            self.move_motor(1, val, '-')
            self.move_motor(2, val, '-')
        elif inst == 'Lower Motor 1':
            self.move_motor(1, val, '-')
        elif inst == 'Raise Motor 2':
            self.move_motor(2, val, '+')
        elif inst == 'Raise Motors 1 and 2':
            self.move_motor(1, val, '+')
            self.move_motor(2, val, '+')
        elif inst == 'Raise Motor 1':
            self.move_motor(1, val, '+')
        elif inst == 'Lower Motor 2':
            self.move_motor(2, val, '-')
        return inst

    def move_motor(self, motor, steps, direction):
        self.Stepper.move_motor(motor, steps, direction)

    def find_center(self, im):
        centers = []
        for n in range(6):
            masked_col = images.mask_img(~im, self.masks[n])
            # images.display(masked_col)
            circles = find_circles(masked_col)
            im = images.draw_circles(im, circles, color=images.PINK,
                                     thickness=1)
            if len(np.shape(circles)) > 1:
                center = np.mean(circles, axis=0)[:2]
            else:
                center = ndimage.measurements.center_of_mass(self.masks[n].transpose())

            im = images.draw_circle(im, center[0], center[1], 5, color=images.PURPLE, thickness=-1)
            centers.append(center)
        # images.display(im)
        centers = np.array(centers)
        mean_center = np.mean(centers, axis=0)
        return mean_center, im

    def annotate_frame(self, im, center, instr, step, steps):
        if len(im.shape) == 2:
            im = np.dstack((im, im, im))
        im = images.draw_circle(im, center[0], center[1], 3, images.PINK)
        im = images.draw_circle(im, self.center[0], self.center[1], 3, images.RED)
        im = images.draw_polygon(im, self.hex, color=images.GREEN, thickness=3)
        font = cv2.FONT_HERSHEY_SIMPLEX
        im = cv2.putText(im, 'Tray Center', (10, 30), font, 1, images.RED, 2, cv2.LINE_AA)
        im = cv2.putText(im, 'Particle Center', (10, 60), font, 1, images.PINK, 2, cv2.LINE_AA)
        im = cv2.putText(im, 'Hexagon', (10, 90), font, 1, images.GREEN, 2, cv2.LINE_AA)
        cv2.putText(im, 'Pixel distance : {:.3f} +/- {:.3f}'.format(self.distance, self.distance_err), (10, 120),font, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(im, instr, (10, 150), font, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(im, '{} of {}'.format(step, steps), (10, 180), font, 1, (255, 255, 255), 2, cv2.LINE_AA)
        for i in range(6):
            im = cv2.putText(im, str(i), (int(self.hex[i, 0]), int(self.hex[i, 1])), font, 1, (255, 255, 255), 2, cv2.LINE_AA)

        return im

    def find_instruction(self, center):
        distances = sp.distance.cdist(np.array([center]), self.hex)[0]
        sort = np.argsort(distances)
        closest = sort[0]

        if closest == 0:
            inst = 'Lower Motors 1 and 2'
        elif closest == 1:
            inst = 'Lower Motor 1'
        elif closest == 2:
            inst = 'Raise Motor 2'
        elif closest == 3:
            inst = 'Raise Motors 1 and 2'
        elif closest == 4:
            inst = 'Raise Motor 1'
        else:
            inst = 'Lower Motor 2'
        return inst


def brightest_circles(circles, im, width=2):
    brightness = []
    for circle in circles:
        small_im = im[int(circle[1])-width:int(circle[1])+width,
                      int(circle[0])-width:int(circle[0])+width]
        brightness.append(np.mean(small_im))
    order = np.flip(np.argsort(brightness))
    return circles[order[:10]]


def find_circles(im):
    YCB = cv2.cvtColor(im, cv2.COLOR_BGR2YCrCb)
    Y = YCB[:, :, 0]
    circles = images.find_circles(Y, 5, 200, 5, 3, 5)
    circles = brightest_circles(circles, Y)
    # im = images.draw_circles(im, circles)
    return circles


def remove_boundary(im):
    col = np.dstack((im, im, im))
    contours, hierarchy = cv2.findContours(im, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(col, contours, -1, (0, 255, 0), 1)
    images.display(col)
    return im

if __name__ == "__main__":
    bal = Balancer(no_of_sides=6)
    # bal.move_motor(1, 100, '+')
    bal.balance()
    # bal.balance()