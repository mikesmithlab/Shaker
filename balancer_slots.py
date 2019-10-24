import time

import cv2
import numpy as np
from scipy import ndimage
from scipy import spatial as sp

import Generic.camera as camera
import Generic.images as images
from Generic.equipment import stepper, arduino

STEPPER_CONTROL = "/dev/serial/by-id/usb-Arduino__www.arduino.cc__0043_5573532393535190E022-if00"


class Balancer:
    """
    Class to balance the shaker using stepper motors and the slots
    """

    def __init__(self, no_of_sides=None, step_size=200):
        cam_num = camera.find_camera_number()
        port = STEPPER_CONTROL
        if no_of_sides is None:
            self.no_of_sides = int(input('Enter the number of sides'))
        else:
            self.no_of_sides = no_of_sides

        self.ard = arduino.Arduino(port)
        self.Stepper = stepper.Stepper(self.ard)
        self.cam = camera.Camera(cam_type='logitechHD1080p', cam_num=cam_num)
        self.hex, self.center, self.contours, im = \
            find_regions(self.cam.single_pic_array())
        images.display(im)
        self.mask, self.masks = self.create_masks()
        self.step_size = step_size

    def create_masks(self):
        im = self.cam.single_pic_array()
        mask = np.zeros(np.shape(im)[:2])
        masks = []
        for contour in self.contours:
            single_mask = np.zeros(np.shape(im)[:2])
            cv2.fillPoly(mask, [contour],  1)
            cv2.fillPoly(single_mask, [contour], 1)
            masks.append(single_mask)
        return mask.astype(np.uint8), np.array(masks).astype(np.uint8)

    def balance(self, repeats=100, delay=5, threshold=2):
        balanced = False
        instruction = ''
        self.distance = 0
        self.distance_err = 0
        cv2.namedWindow('Levelling', cv2.WINDOW_KEEPRATIO)
        cv2.resizeWindow('Levelling', 1280, 720)
        while balanced is False:
            centers = []
            for f in range(repeats):
                im = self.cam.single_pic_array()
                center, im = self.find_center(im)
                centers.append(center)
                self.current_center = np.mean(centers, axis=0)
                im = self.annotate_frame(im, center, instruction, f+1, repeats)
                cv2.imshow('Levelling', im)
                if cv2.waitKey(100) & 0xFF == ord('q'):
                    balanced = True
                    print('Balancing Quit')
                    break
            if balanced is False:
                center = np.mean(centers, axis=0)
                distances = sp.distance.cdist(
                    centers, np.reshape(self.center, (1, 2)))
                self.distance = np.mean(distances)
                self.distance_err = np.std(distances)
                instruction = self.find_instruction(center)

                if self.distance > threshold:
                    self.run_instruction(instruction)
                    self.delay_view(delay, instruction)
                else:
                    print('Balanced')
                    balanced = True

    def delay_view(self, delay, instruction):
        for t in range(2*delay):
            s = time.time()
            im = self.cam.single_pic_array()
            center, im = self.find_center(im)
            im = self.annotate_frame(
                im, center, instruction, 'Delay', delay - t/2)
            cv2.imshow('Levelling', im)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
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
            circles = find_circles(masked_col)
            im = images.draw_circles(im, circles, color=images.PINK,
                                     thickness=1)
            if len(np.shape(circles)) > 1:
                center = np.mean(circles, axis=0)[:2]
            else:
                center = ndimage.measurements.center_of_mass(
                    self.masks[n].transpose())
            im = images.draw_circle(im, center[0], center[1], 5,
                                    color=images.PURPLE, thickness=-1)
            centers.append(center)
        centers = np.array(centers)
        mean_center = np.mean(centers, axis=0)
        return mean_center, im

    def annotate_frame(self, im, center, instr, step, steps):
        if len(im.shape) == 2:
            im = np.dstack((im, im, im))
        im = images.draw_circle(im, self.current_center[0],
                                self.current_center[1], 5,
                                color=images.ORANGE, thickness=-1)
        im = images.draw_circle(im, center[0], center[1], 3, images.PINK)
        im = images.draw_circle(im, self.center[0], self.center[1], 3,
                                images.RED)
        im = images.draw_polygon(im, self.hex, color=images.GREEN, thickness=3)
        font = cv2.FONT_HERSHEY_SIMPLEX
        im = cv2.putText(im, 'Tray Center', (10, 30), font, 1, images.RED, 2,
                         cv2.LINE_AA)
        im = cv2.putText(im, 'Particle Center', (10, 60), font, 1, images.PINK,
                         2, cv2.LINE_AA)
        im = cv2.putText(im, 'Average Center', (10, 90), font, 1, images.ORANGE,
                         2, cv2.LINE_AA)
        im = cv2.putText(im, 'Hexagon', (10, 120), font, 1, images.GREEN, 2,
                         cv2.LINE_AA)
        cv2.putText(
                im, 'Pixel distance : {:.3f} +/- {:.3f}'.format(
                self.distance, self.distance_err), (10, 150), font, 1,
                (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(im, instr, (10, 180), font, 1, (255, 255, 255), 2,
                    cv2.LINE_AA)
        cv2.putText(im, '{} of {}'.format(step, steps), (10, 210), font, 1,
                    (255, 255, 255), 2, cv2.LINE_AA)
        for i in range(6):
            im = cv2.putText(
                    im, str(i), (int(self.hex[i, 0]), int(self.hex[i, 1])),
                    font, 1, (255, 255, 255), 2, cv2.LINE_AA)

        return im

    def find_instruction(self, center):
        distances = sp.distance.cdist(np.array([center]), self.hex)[0]
        sort = np.argsort(distances)
        closest = sort[0]

        if closest == 3:
            inst = 'Lower Motors 1 and 2'
        elif closest == 4:
            inst = 'Lower Motor 1'
        elif closest == 5:
            inst = 'Raise Motor 2'
        elif closest == 0:
            inst = 'Raise Motors 1 and 2'
        elif closest == 1:
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


def find_regions(image):
    # blue = images.find_color(image, 'Blue')
    blue = find_blue(image)
    # Find contours and sort by area
    contours = images.find_contours(blue)
    temp = images.draw_contours(image, contours)
    images.display(temp)
    contours = images.sort_contours(contours)
    # Second biggest contour is the hexagonal boundary
    # Find center of hexagon using circle
    hex_corners, (xc, yc) = images.find_contour_corners(contours[-2], 6,
                                                        aligned=True)
    hex_corners = contours[-2][hex_corners]
    slot_hulls = [cv2.convexHull(contours[-n]) for n in np.arange(3, 9)]

    # Annotate image
    image = images.draw_contours(image, slot_hulls)
    image = images.draw_polygon(image, hex_corners, thickness=2)
    image = images.draw_circle(image, int(xc), int(yc), 6, color=images.BLUE)
    hex_corners = np.squeeze(np.array(hex_corners))

    return hex_corners, (xc, yc), slot_hulls, image


def find_blue(im):
    hsv_im = cv2.cvtColor(im, cv2.COLOR_RGB2HSV)
    mask = cv2.inRange(hsv_im, (0, 0, 0), (50, 255, 255))
    blue = cv2.bitwise_and(im, im, mask=mask)
    blue = images.bgr_2_grayscale(blue)
    return blue


def find_circles(im):
    gray = images.bgr_2_grayscale(im)
    # images.threshold_slider(gray)
    # images.Circle_GUI(gray)
    circles = images.find_circles(gray, 6, 200, 3, 4, 5)
    circles = brightest_circles(circles, gray)
    im = images.draw_circles(im, circles, color=images.RED)
    # images.display(im)
    return circles


def remove_boundary(im):
    col = np.dstack((im, im, im))
    contours, hierarchy = cv2.findContours(
        im, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(col, contours, -1, (0, 255, 0), 1)
    images.display(col)
    return im

if __name__ == "__main__":
    bal = Balancer(no_of_sides=6, step_size=25)
    bal.balance(repeats=200, delay=60, threshold=5)