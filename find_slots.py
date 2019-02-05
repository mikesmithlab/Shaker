from Generic import images
import numpy as np
import cv2
from math import pi
import scipy.spatial as sp

def find_regions(image, bottom, top):
    # subtract red from blue
    difference = image[:, :, 0] - image[:, :, 2]
    _, difference = cv2.threshold(difference, bottom, 255,
                                  type=cv2.THRESH_TOZERO)
    _, difference = cv2.threshold(difference, top, 255,
                                  type=cv2.THRESH_TOZERO_INV)
    binary = images.adaptive_threshold(difference, 131)

    contours, hiererchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    area = []
    for cnt in contours:
        area.append(cv2.contourArea(cnt))
    area_sort = np.argsort(area)

    hex = contours[area_sort[-2]]
    (xc, yc), r = cv2.minEnclosingCircle(hex)
    hex = np.squeeze(hex)

    angles = np.zeros(len(hex))
    for i, p in enumerate(hex):
        angles[i] = np.arctan2(p[0]-xc, p[1]-yc)
    angles *= 180/pi

    dists = sp.distance.cdist(np.array([[xc, yc]]), hex)
    dists = np.squeeze(dists)
    corners = []
    for segment in range(6):
        index = np.nonzero(~((angles >= (-180 + 60 * segment)) * (
                    angles < (-120 + 60 * segment))))
        temp_dists = dists.copy()
        temp_dists[index] = 0
        sort_list = np.argsort(temp_dists)
        corners.append(sort_list[-1])

    for corner in corners:
        center = (int(hex[corner, 0]), int(hex[corner, 1]))
        image = cv2.circle(image, center, int(4), (0, 255, 0), 2)

    hex_corners = np.array(corners)

    slot_corners = []
    for n in np.arange(3, 9):
        rect = cv2.minAreaRect(contours[area_sort[-n]])
        box = cv2.boxPoints(rect)
        box = np.int0(box)
        slot_corners.append(box)
        image = cv2.drawContours(image, [box], 0, (0, 255, 0), 2)

    images.display(image)
    return hex_corners, np.array(slot_corners)


def sort_slots(slots):
    mean_pos = np.mean(slots, axis=1)
    angles = np.arctan2(mean_pos[:, 1], mean_pos[:, 0])
    return slots[np.argsort(angles)]


if __name__ == "__main__":
    image = images.load_img('frame.png')
    hex_corners, slot_corners = find_regions(image, 10, 180)
    slots = sort_slots(slot_corners)
