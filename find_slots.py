from Generic import images
import numpy as np
import cv2
from math import pi
import scipy.spatial as sp
import matplotlib.pyplot as plt


def find_regions(image):
    blue = images.find_color(image, 'Blue')
    images.display(blue)
    # Find contours and sort by area
    contours = images.find_contours(blue)
    contours = images.sort_contours(contours)
    # Second biggest contour is the hexagonal boundary
    # Find center of hexagon using circle
    # hex_corners, (xc, yc) = find_hex_info(contours[-2])
    hex_corners, (xc, yc) = images.find_contour_corners(contours[-2], 6,
                                                        aligned=True)
    hex_corners = contours[-2][hex_corners]
    slot_hulls = find_slot_info(contours)

    # Annotate image
    image = images.draw_contours(image, slot_hulls)
    image = images.draw_polygon(image, hex_corners, thickness=2)
    image = images.draw_circle(image, int(xc), int(yc), 6, color=images.BLUE)

    return hex_corners, (xc, yc), slot_hulls, image


def find_slot_info(contours):
    hulls = []
    for n in np.arange(3, 9):
        cnt = contours[-n]
        hull = cv2.convexHull(cnt)
        hulls.append(hull)
    return hulls


# def find_hex_info(cnt):
#     (xc, yc), r = cv2.minEnclosingCircle(cnt)
#     cnt = np.squeeze(cnt)
#     corners = find_hex_corners(cnt, xc, yc)
#     hex_corners = np.array(cnt[corners])
#     return hex_corners, (xc, yc)


# def refine_slot_contour(cnt, im):
#     cnt = cv2.convexHull(cnt)
#     mask = np.zeros(np.shape(im)[:2], dtype=np.uint8)
#     cv2.fillPoly(mask, [cnt], 1)
#     masked = images.mask_img(~im, mask)
#     masked = images.bgr_2_grayscale(masked)
#     masked = images.adaptive_threshold(masked, 31, 0)
#     images.display(masked)
#     contours = images.find_contours(masked)
#     contours = sort_contours(contours)
#     hull = cv2.convexHull(contours[-2])
#     masked = images.draw_contours(masked, [hull])
#     masked = cv2.drawContours(np.dstack((masked, masked, masked)), [hull], 0, (0, 255, 0))
#     images.display(masked)
#     return contours[-2]


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


# def sort_contours(contours):
#     area = []
#     for cnt in contours:
#         area.append(cv2.contourArea(cnt))
#     sorted = np.argsort(area)
#     contours_new = []
#     for arg in sorted:
#         contours_new.append(contours[arg])
#     return contours_new


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
    hex, center, hulls, im = find_regions(image)
    print(hex.shape)
    # print(slots.shape)
    images.display(im)
