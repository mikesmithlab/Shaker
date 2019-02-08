from Generic import images
import numpy as np
import cv2
from math import pi
import scipy.spatial as sp
import matplotlib.pyplot as plt


def find_regions(image, tol=10):
    # Find the pixels in image that have blue pixels with values of at least
    # 10 above the mean and set them to white in a binary image
    mean = np.median(image, axis=2)
    set_high = np.nonzero(image[:, :, 0] > mean + tol)
    new_image = np.zeros(np.shape(image)[:2], dtype=np.uint8)
    new_image[set_high] = 255

    # Find contours and sort by area
    contours, _ = cv2.findContours(new_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sort_contours(contours)

    # Second biggest contour is the hexagonal boundary
    # Find center of hexagon using circle

    hex = contours[-2]
    (xc, yc), r = cv2.minEnclosingCircle(hex)
    hex = np.squeeze(hex)



    corners = find_hex_corners(hex, xc, yc)
    for corner in corners:
        center = (int(hex[corner, 0]), int(hex[corner, 1]))
        image = cv2.circle(image, center, int(4), (0, 255, 0), 2)

    hex_corners = np.array(hex[corners])


    # Slots should be the next 6 biggest contours
    # Save the coordinates of the bounding boxes
    slot_corners = []
    slot_hulls = []
    for n in np.arange(3, 9):
        contour = refine_slot_contour(contours[-n], image)
        slot_hulls.append(cv2.convexHull(contour))
        rect = cv2.minAreaRect(contour)
        box = cv2.boxPoints(rect)
        box = np.int0(box)
        slot_corners.append(box)
        image = cv2.drawContours(image, [box], 0, (0, 255, 0), 2)

    slot_corners = sort_slots(np.array(slot_corners))

    image = cv2.drawContours(image, [hex], 0, (0, 255, 0), 2)
    image = cv2.circle(image, (int(xc), int(yc)), int(r), (255, 0, 0), 2)

    return hex_corners, slot_corners, (xc, yc), slot_hulls, image


def refine_slot_contour(cnt, im):
    cnt = cv2.convexHull(cnt)
    mask = np.zeros(np.shape(im)[:2], dtype=np.uint8)
    cv2.fillPoly(mask, [cnt], 1)
    masked = images.mask_img(~im, mask)
    masked = images.bgr_2_grayscale(masked)
    masked = images.adaptive_threshold(masked, 31, 0)
    contours, _ = cv2.findContours(masked, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sort_contours(contours)
    masked = cv2.drawContours(np.dstack((masked, masked, masked)), [contours[-2]], 0, (0, 255, 0))
    return contours[-2]


def find_hex_corners(hex, xc, yc):

    # Calculate the angles of all the contour points
    angles = np.arctan2(hex[:, 1]-yc, hex[:, 0]-xc)
    angles = angles * 180/pi
    # Find distance between all contour points and the centre of the hex
    dists = sp.distance.cdist(np.array([[xc, yc]]), hex)
    dists = np.squeeze(dists)

    # Find the furthest point in 6 60 degree segments which are the corners
    corners = []
    for segment in range(6):
        if segment != 5:
            index = np.nonzero(~((angles >= (-150 + 60 * segment)) * (
                        angles < (-90 + 60 * segment))))
        else:
            index = np.nonzero((angles >= -150) * (angles < 150))
        temp_dists = dists.copy()
        temp_dists[index] = 0
        sort_list = np.argsort(temp_dists)
        corners.append(sort_list[-1])
    return corners


def sort_contours(contours):
    area = []
    for cnt in contours:
        area.append(cv2.contourArea(cnt))
    sorted = np.argsort(area)
    contours_new = []
    for arg in sorted:
        contours_new.append(contours[arg])
    return contours_new


def sort_slots(slots):
    mean_pos = np.mean(slots, axis=1)
    angles = np.arctan2(mean_pos[:, 1], mean_pos[:, 0])
    return slots[np.argsort(angles)]


if __name__ == "__main__":
    from Generic import camera
    cam_num = camera.find_camera_number()
    webcam = camera.Camera(cam_type='logitechHD1080p', cam_num=cam_num)
    image = webcam.single_pic_array()
    # image = images.load_img('frame.png')
    hex, slots, center, hulls, im = find_regions(image)
    print(hex.shape)
    print(slots.shape)
    images.display(im)
