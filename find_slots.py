from Generic import images
import numpy as np
import cv2


def find_regions(image):
    blue = images.find_color(image, 'Blue')
    # Find contours and sort by area
    contours = images.find_contours(blue)
    contours = images.sort_contours(contours)
    # Second biggest contour is the hexagonal boundary
    # Find center of hexagon using circle
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


def sort_slots(slots):
    mean_pos = np.mean(slots, axis=1)
    angles = np.arctan2(mean_pos[:, 1], mean_pos[:, 0])
    return slots[np.argsort(angles)]


if __name__ == "__main__":
    from Generic import camera
    cam_num = camera.find_camera_number()
    webcam = camera.Camera(cam_type='logitechHD1080p', cam_num=cam_num)
    image = webcam.single_pic_array()
    hex, center, hulls, im = find_regions(image)
    print(hex.shape)
    images.display(im)
