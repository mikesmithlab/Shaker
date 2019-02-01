from Generic import camera
from Generic import images
import matplotlib.pyplot as plt
import numpy as np
import cv2
from math import pi
import scipy.spatial as sp

cam = camera.Camera()
frame = cam.single_pic_array()
frame = frame[182:829, 654:1320, :]

# plt.figure()
# plt.subplot(2, 2, 1)
# plt.imshow(frame[:, :, 0], cmap=plt.cm.get_cmap('gray'))
# plt.title('blue')
# plt.subplot(2, 2, 2)
# plt.imshow(frame[:, :, 1], cmap=plt.cm.get_cmap('gray'))
# plt.title('green')
# plt.subplot(2, 2, 3)
# plt.imshow(frame[:, :, 2], cmap=plt.cm.get_cmap('gray'))
# plt.title('red')
# plt.subplot(2, 2, 4)
# plt.imshow(np.dstack((frame[:, :, 2], frame[:, :, 1], frame[:, :, 0])))
# plt.show()

difference = frame[:, :, 0] - frame[:, :, 2]
images.display(difference)
_, difference = cv2.threshold(difference, 40, 255, type=cv2.THRESH_TOZERO)
_, difference = cv2.threshold(difference, 180, 255, type=cv2.THRESH_TOZERO_INV)
# images.display(difference)
ret, thresh = cv2.threshold(difference, 20, 255, type=cv2.THRESH_BINARY)
images.display(thresh)
contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
area = []
for i, cnt in enumerate(contours):
    area.append(cv2.contourArea(cnt))
big = np.argsort(area)

hex = contours[big[-2]]
# print(area)
frame = cv2.drawContours(frame, contours, big[-2], (255, 0, 0), 3)
frame = cv2.drawContours(frame, contours, big[-3], (255, 0, 0), 3)
frame = cv2.drawContours(frame, contours, big[-4], (255, 0, 0), 3)



(xc, yc), r = cv2.minEnclosingCircle(hex)

hex = np.squeeze(hex)

angles = np.zeros(len(hex))
for i, p in enumerate(hex):
    angles[i] = np.arctan2(p[0]-xc, p[1]-yc)
angles = angles * 180/pi

dists = sp.distance.cdist(np.array([[xc, yc]]), hex)

dists = np.squeeze(dists)
corners = []
for segment in range(6):
    index = np.nonzero(~((angles >= (-180 + 60*segment)) * (angles < (-120 + 60*segment))))
    temp_dists = dists.copy()
    temp_dists[index] = 0
    sort_list = np.argsort(temp_dists)
    corners.append(sort_list[-1])
print(corners)

for corner in corners:
    center = (int(hex[corner, 0]), int(hex[corner, 1]))
    frame = cv2.circle(frame, center, int(4), (0, 255, 0), 2)

for n in np.arange(3, 5):
    rect = cv2.minAreaRect(contours[big[-n]])
    box = cv2.boxPoints(rect)
    box = np.int0(box)
    frame = cv2.drawContours(frame, [box], 0, (0, 255, 0), 2)



# images.display(difference)
images.display(frame)