from Generic import images
import numpy as np
import cv2
from math import pi
import scipy.spatial as sp
import matplotlib.pyplot as plt

def find_regions(image, bottom, top):
    # Subtract red channel from blue to channel.
    # Remove grays from top and bottom of image
    difference = image[:, :, 0] - image[:, :, 2]
    _, difference = cv2.threshold(difference, bottom, 255,
                                  type=cv2.THRESH_TOZERO)
    _, difference = cv2.threshold(difference, top, 255,
                                  type=cv2.THRESH_TOZERO_INV)
    binary = images.adaptive_threshold(difference, 131)

    # Find contours and sort by area
    contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    area = []
    for cnt in contours:
        area.append(cv2.contourArea(cnt))
    area_sort = np.argsort(area)

    # Second biggest contour is the hexagonal boundary
    # Find center of hexagon using circle
    hex = contours[area_sort[-2]]
    image = cv2.drawContours(image, [hex], 0, (0, 255, 0), 2)
    (xc, yc), r = cv2.minEnclosingCircle(hex)
    image = cv2.circle(image, (int(xc), int(yc)), int(r), (255, 0, 0), 2)
    hex = np.squeeze(hex)

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

    for corner in corners:
        center = (int(hex[corner, 0]), int(hex[corner, 1]))
        image = cv2.circle(image, center, int(4), (0, 255, 0), 2)

    hex_corners = np.array(hex[corners])

    # Slots should be the next 6 biggest contours
    # Save the coordinates of the bounding boxes
    slot_corners = []
    slot_hulls = []
    for n in np.arange(3, 9):
        slot_hulls.append(cv2.convexHull(contours[area_sort[-n]]))
        rect = cv2.minAreaRect(contours[area_sort[-n]])
        box = cv2.boxPoints(rect)
        box = np.int0(box)
        slot_corners.append(box)
        image = cv2.drawContours(image, [box], 0, (0, 255, 0), 2)

    slot_corners = sort_slots(np.array(slot_corners))

    return hex_corners, slot_corners, (xc, yc), slot_hulls, image


def sort_slots(slots):
    mean_pos = np.mean(slots, axis=1)
    angles = np.arctan2(mean_pos[:, 1], mean_pos[:, 0])
    return slots[np.argsort(angles)]


if __name__ == "__main__":
    image = images.load_img('frame.png')
    hex, slots, center, im = find_regions(image, 10, 180)
    print(hex.shape)
    print(slots.shape)
    images.display(im)
