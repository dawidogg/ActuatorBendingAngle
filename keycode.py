import cv2
import sys
import numpy 

cv2.imshow("Key code script", numpy.empty((1, 1)))
while cv2.getWindowProperty("Key code script", 0) >= 0:
    res = cv2.waitKey(0)
    print('You pressed %d (0x%x), LSB: %d (%s)' % (res, res, res % 256,
    repr(chr(res%256)) if res%256 < 128 else '?'))
