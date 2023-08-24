import cv2
import numpy

BLUR_FACTOR = 5
KERNEL = numpy.array([
    [-1, -1, -1],
    [-1,  10, -1],
    [-1, -1, -1]
])
MARKER_THRESHOLD = 220

IMG_PATH = "./img/perspective_1.png" 
orig = cv2.imread(IMG_PATH, cv2.IMREAD_REDUCED_COLOR_2)
frame = cv2.imread(IMG_PATH, cv2.IMREAD_REDUCED_COLOR_2)

frame = numpy.array(frame[:,:,0])
frame = cv2.medianBlur(frame, BLUR_FACTOR)
cv2.filter2D(frame, -1, KERNEL, frame)
# frame = cv2.medianBlur(frame, BLUR_FACTOR)
thresh = cv2.threshold(frame, 70, 255, cv2.THRESH_BINARY_INV)[1]

contours = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]
contours = sorted(contours, key = lambda x: cv2.arcLength(x, True), reverse=True)
        
frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
i = 0
white_squares = []
centers = []
for c in contours:
    epsilon = 0.1 * cv2.arcLength(c, True)
    approx = cv2.approxPolyDP(c, epsilon, True)

    mask = numpy.zeros_like(frame[:, :, 0])
    cv2.drawContours(mask, [approx], -1, 255, -1)
    mean = cv2.mean(frame, mask=mask)
    if (mean[0] > MARKER_THRESHOLD):
        white_squares.append(approx)
        m = cv2.moments(approx)
        try:
            x = int(m["m10"] / m["m00"]) 
            y = int(m["m01"] / m["m00"]) 
            centers.append([[x, y, 1]])
        except:
            pass
    i += 1
    if i >= 6:
        break


for ws in white_squares:    
    cv2.drawContours(frame, [ws], -1, (255, 0, 0), 2)

new_white_squares = []
for ws in white_squares:
    flat_points = numpy.ndarray.flatten(numpy.array(ws))
    paired_points = []
    for i in range(0, len(flat_points), 2):
        paired_points.append([flat_points[i], flat_points[i+1]])
    new_white_squares.append(numpy.float32(paired_points))
white_squares = new_white_squares

center = [int(frame.shape[1]/2), int(frame.shape[0]/2)]
center = [0, 0]
pts2 = [center,
        [0, 0],
        [center[0]+10, center[1]+10],
        [0, 0]]
pts2[1] = [pts2[0][0], pts2[2][1]]
pts2[3] = [pts2[2][0], pts2[0][1]]
pts2 = numpy.float32(pts2)

matrix = cv2.getPerspectiveTransform(white_squares[0], pts2)
result = cv2.warpPerspective(orig, matrix, (orig.shape[1], orig.shape[0]))

centers = numpy.array(centers)
print(centers)
for c in centers:
    c = [c[0][0], c[0][1]]
    cv2.circle(frame, c, 4, (0, 0, 255), -1)
cv2.imshow("Perspective transform", frame)
cv2.waitKey()
cv2.destroyAllWindows()


for i in range(3):
    
    matrix = cv2.getPerspectiveTransform(white_squares[i], pts2)
    matrix[2][0:2] = [0, 0]
    matrix[0][2] = orig.shape[1]/3
    matrix[1][2] = orig.shape[0]/3
    result = cv2.warpPerspective(orig, matrix, (orig.shape[1], orig.shape[0]))
    centers_copy = centers.copy()
    print(matrix)
    print(centers_copy)

    for c in centers_copy:
        c = numpy.matmul(matrix, c[0])
        print(c)
        c = [int(c[0]), int(c[1])]
        cv2.circle(result, c, 4, (0, 0, 255), -1)
    print("------------------------------------------------------------")
    cv2.imshow("Perspective transform", result)
    cv2.waitKey()
    cv2.destroyAllWindows()

