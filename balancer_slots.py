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
        self.hex, slots, self.center, self.contours, im = find_slots.find_regions(self.webcam.single_pic_array())
        images.display(im)
        self.mask, self.masks = self.create_masks(slots)
        self.step_size = step_size

    def create_masks(self, slots):
        im = self.webcam.single_pic_array()
        mask = np.zeros(np.shape(im)[:2])
        masks = []
        for slot, contour in zip(slots, self.contours):
            single_mask = np.zeros(np.shape(im)[:2])
            slot = slot.reshape(4, 1, 2)
            cv2.fillPoly(mask, [slot],  1)
            cv2.fillPoly(single_mask, [contour], 1)
            masks.append(single_mask)
        return mask.astype(np.uint8), np.array(masks).astype(np.uint8)

    def balance(self, repeats=10, delay=1):
        balanced = False
        while balanced is False:
            centers = []
            for f in range(repeats):
                im = self.webcam.single_pic_array()
                center, im = self.find_center(im)
                centers.append(center)
            center = np.mean(centers, axis=0)
            self.distance = sp.distance.pdist([center, self.center])
            instruction = self.find_instruction(center)
            print(instruction)
            im = self.annotate_frame(im, center, instruction)
            cv2.imshow('', im)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                balanced = True
            if self.distance < 2:
                balanced = True
                print('Centre of mass distance less than 2 pixels')
            else:
                # self.run_instruction(instruction)
                time.sleep(delay)

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
            masked = images.bgr_2_grayscale(masked_col)
            masked = images.threshold(masked, 200)
            masked = images.erode(masked, (9, 9))
            # images.display(masked)
            center = ndimage.measurements.center_of_mass(masked.transpose())
            if np.isnan(center[0]):
                # images.display(self.masks[n])
                center = ndimage.measurements.center_of_mass(self.masks[n].transpose())
            try:
                im = images.draw_circle(im, center[0], center[1], 5, color=images.PURPLE, thickness=-1)
            except ValueError as err:
                print(err)
                print('center is ({},{})'.format(center[0], center[1]))
                plt.figure()
                plt.imshow(masked)
                plt.show()
            centers.append(center)
        centers = np.array(centers)
        mean_center = np.mean(centers, axis=0)
        return mean_center, im

    def annotate_frame(self, im, center, instr):
        if len(im.shape) == 2:
            im = np.dstack((im, im, im))
        im = images.draw_circle(im, center[0], center[1], 3, images.PINK)
        im = images.draw_circle(im, self.center[0], self.center[1], 3, images.RED)
        im = images.draw_polygon(im, self.hex, color=images.GREEN, thickness=3)
        font = cv2.FONT_HERSHEY_SIMPLEX
        im = cv2.putText(im, 'Tray Center', (10, 30), font, 1, images.RED, 2, cv2.LINE_AA)
        im = cv2.putText(im, 'Particle Center', (10, 60), font, 1, images.PINK, 2, cv2.LINE_AA)
        im = cv2.putText(im, 'Hexagon', (10, 90), font, 1, images.GREEN, 2, cv2.LINE_AA)
        cv2.putText(im, 'Pixel distance : {:.3f}'.format(self.distance[0]), (10, 120),font, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(im, instr, (10, 150), font, 1, (255, 255, 255), 2, cv2.LINE_AA)
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



if __name__ == "__main__":
    bal = Balancer(no_of_sides=6)
    # bal.move_motor(1, 100, '+')
    bal.balance()
    # bal.balance()