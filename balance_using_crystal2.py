import datetime
import os

import cv2
import numpy as np
from scipy import spatial

from Generic import camera, images
from Generic.equipment import arduino, stepper
from Shaker import power

STEPPER_CONTROL = "/dev/serial/by-id/usb-Arduino__www.arduino.cc__0043_5573532393535190E022-if00"


class Balancer:

    def __init__(self, step_size=50):
        now = datetime.datetime.now()
        self.log_direc = "/media/data/Data/Logs/{}_{}_{}_{}_{}/".format(
            now.year, now.month, now.day, now.hour, now.minute)
        os.mkdir(self.log_direc)
        self.i = 0
        self.shaker = power.PowerSupply()
        self.shaker.change_duty(750)
        self.step_size = step_size
        cam_num = camera.find_camera_number()
        port = STEPPER_CONTROL
        self.ard = arduino.Arduino(port)
        self.motors = stepper.Stepper(self.ard)
        self.cam = camera.Camera(cam_type='logitechHD1080p', cam_num=cam_num)
        im = self.cam.single_pic_array()
        self.hex, self.center, self.crop, self.mask = self.find_hexagon(im)
        im = images.crop_and_mask_image(im, self.crop, self.mask)
        self.im_shape = im.shape
        im = images.draw_polygon(im, self.hex)
        im = images.draw_circle(im, self.center[0], self.center[1], 3)
        images.display(im)

    def find_hexagon(self, im):
        crop_shape = images.CropShape(im, 6)
        mask, crop, boundary, points = crop_shape.begin_crop()

        points[:, 0] -= crop[0][0]
        points[:, 1] -= crop[0][1]
        center = np.mean(points, axis=0)
        return points, center, crop, mask

    def balance(self, repeats=5, threshold=10):
        balanced = False
        window = images.Displayer('Levelling')
        center = (0, 0)
        distance = 0
        while balanced is False:
            centers = []
            for f in range(repeats):
                self.f = f
                self.shaker.ramp(900, 730, 1, record=False, stop_at_end=False)
                mean_im = self.mean_im()
                center = self.find_center(mean_im)
                centers.append(center)
                mean_center = np.mean(centers, axis=0).astype(np.int32)
                annotated_im = self.annotate_image(mean_im, center,
                                                   mean_center, distance,
                                                   centers)
                window.update_im(annotated_im)

            # mean_im = images.mean(ims)
            # center = self.find_center(mean_im)
            mean_center = np.mean(centers, axis=0).astype(np.int32)
            instruction, distance = self.find_instruction(mean_center)
            annotated_im = self.annotate_image(mean_im, center, mean_center,
                                               distance, centers)
            window.update_im(annotated_im)
            if distance > threshold:
                self.run_instruction(instruction)
            else:
                balanced = True
                print('BALANCED')

    def run_instruction(self, instruction):
        val = self.step_size
        if instruction == 'Lower Motors 1 and 2':
            self.move_motor(1, val, '-')
            self.move_motor(2, val, '-')
        elif instruction == 'Lower Motor 1':
            self.move_motor(1, val, '-')
        elif instruction == 'Raise Motor 2':
            self.move_motor(2, val, '+')
        elif instruction == 'Raise Motors 1 and 2':
            self.move_motor(1, val, '+')
            self.move_motor(2, val, '+')
        elif instruction == 'Raise Motor 1':
            self.move_motor(1, val, '+')
        elif instruction == 'Lower Motor 2':
            self.move_motor(2, val, '-')

    def move_motor(self, motor, steps, direction):
        self.motors.move_motor(motor, steps, direction)

    def find_instruction(self, center):
        # center = np.mean(centers, axis=0)
        distance = ((center[0] - self.center[0]) ** 2 + (
                    center[1] - self.center[1]) ** 2) ** 0.5
        corner_dists = spatial.distance.cdist(np.array(center).reshape(1, 2),
                                              self.hex)
        closest_corner = np.argmin(corner_dists)
        instructions = {0: 'Raise Motor 2',
                        1: 'Raise Motors 1 and 2',
                        2: 'Raise Motor 1',
                        3: 'Lower Motor 2',
                        4: 'Lower Motors 1 and 2',
                        5: 'Lower Motor 1'}
        self.set_step_size(distance)
        return instructions[closest_corner], distance

    def set_step_size(self, distance):
        if distance > 50:
            self.step_size = 200
        elif distance > 40:
            self.step_size = 150
        elif distance > 30:
            self.step_size = 100
        elif distance > 20:
            self.step_size = 50
        elif distance > 10:
            self.step_size = 25
        else:
            self.step_size = 10

    def find_center(self, im):
        # images.save(im, 'test.png')
        im0 = im.copy()
        im = images.threshold(im, 140)
        im = images.dilate(im, (5, 5))
        im = images.opening(im, (21, 21))
        center = images.center_of_mass(im)
        im0 = images.draw_circle(im0, center[0], center[1], 5)
        im = images.draw_circle(im, center[0], center[1], 5)
        images.save(images.hstack(im, im0),
                    self.log_direc + '{}.png'.format(self.i))
        self.i += 1
        return center

    def mean_im(self):
        ims = []
        for f in range(8):
            im = ~self.cam.single_pic_array()
            im = images.crop_and_mask_image(im, self.crop, self.mask)
            if f == 0:
                ring_mask = images.inrange(images.bgr_to_lab(im), (0, 113, 0),
                                           (255, 152, 255))
            im = images.bgr_2_grayscale(im)
            ims.append(im)
        mean_im = images.mean(ims)
        mean_im = images.mask_img(mean_im, ring_mask)
        return mean_im

    def annotate_image(self, im, current_center, mean_center, distance,
                       centers):
        im = im.copy()
        if len(im.shape) == 2:
            im = images.stack_3(im)
        im = images.draw_circle(im, current_center[0], current_center[1], 5,
                                color=images.ORANGE, thickness=-1)
        im = images.draw_circle(im, self.center[0], self.center[1], 5,
                                images.RED)
        im = images.draw_circle(im, mean_center[0], mean_center[1], 5,
                                images.BLUE)
        font = cv2.FONT_HERSHEY_SIMPLEX
        im = cv2.putText(im, 'Tray Center', (10, 30), font, .5, images.RED, 2,
                         cv2.LINE_AA)
        im = cv2.putText(im, 'Current Center', (10, 60), font, .5,
                         images.ORANGE, 2, cv2.LINE_AA)
        im = cv2.putText(im, 'Mean Center', (10, 90), font, .5, images.BLUE, 2,
                         cv2.LINE_AA)
        im = cv2.putText(im, 'Pixel distance : {:.3f}'.format(
            distance), (10, 120), font, .5, images.GREEN, 2, cv2.LINE_AA)
        im = cv2.putText(im, 'Repeat: {}'.format(self.f), (10, 150), font, .5,
                         images.GREEN, 2, cv2.LINE_AA)
        for center in centers:
            im = images.draw_circle(im, center[0], center[1], 5, images.YELLOW)
        im = cv2.putText(im, 'Old Centers', (10, 180), font, .5, images.YELLOW,
                         2, cv2.LINE_AA)
        return im


if __name__ == "__main__":
    balancer = Balancer()
    balancer.balance(repeats=100)
