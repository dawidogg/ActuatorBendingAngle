import cv2
import numpy
import enum
import time
import random 
import csv
import os
from enum import Enum

class Application(object):
    # constants
    BLUR_FACTOR = 5
    KERNEL = numpy.array([
        [-1, -1, -1],
        [-1,  11, -1],
        [-1, -1, -1]
    ])
    MARKER_THRESHOLD = 200
    MARKER_COLORS = [(0, 0, 255), (0, 170, 0), (255, 0, 0)]
    LINE_COLOR = (0, 0, 0)
    LINE_WIDTH = 2
    MARKER_WIDTH = 4
    MARKER_CENTER_WIDTH = 7

    class INPUT_TYPE(Enum):
        Camera = 0
        CSV = 1          

    # public methods
    def __init__(self, name):
        self.name = name
        cv2.namedWindow(self.name)
        self.prev_points = [(0, 0), (0, 0), (0, 0)]
        self.mid_point = 0
        self.angle = 0
        self.calibrating_state = True
        self.output_mode = False
        self.csv_queue = []
        
    def setCamera(self, source):
        self.input_source = Application.INPUT_TYPE.Camera
        self.video_capture = cv2.VideoCapture(source)
        self.__getFrame()
        
    def setInputFile(self, source):
        self.input_source = Application.INPUT_TYPE.CSV
        self.input_file_template = source + '/' + source[source.rfind('/')+1 :]
        self.input_file_csv = open(self.input_file_template+".csv", mode="r")
        self.input_reader = csv.reader(self.input_file_csv)
        next(self.input_reader)
        self.success = 1
                
    def setOutputFile(self, source):
        self.output_dir = source
        if os.path.exists(source):
            if os.name == "posix": # Linux
                os.system(f"rm -r {source}")
            if os.name == "nt": # Windows
                os.system(f"rmdir {source}") 
        os.makedirs(self.output_dir)
        self.output_file_template = self.output_dir + '/' + self.output_dir[self.output_dir.rfind('/')+1 :]
        self.output_file_csv = open(self.output_file_template+".csv", mode="w")
        self.output_writer = csv.writer(self.output_file_csv)
        head = ["x1", "y1", "x2", "y2", "x3", "y3", "mid", "angle","orig_path", "marked_path"]
        self.output_writer.writerow(head)
                
    def close(self):
        cv2.destroyWindow(self.name)
        if self.input_source == Application.INPUT_TYPE.Camera:
            self.video_capture.release()
        if self.input_source == Application.INPUT_TYPE.CSV:
            self.input_file_csv.close()
        if self.output_mode:
            self.output_file_csv.close()

    def run(self):
        self.__getFrame()
        self.points_success =  self.__findPoints()
        if self.points_success:
            self.__findAngle()
        self.__drawWindow()
        return self.__keyboardResponse()
    
    # private methods
    def __findPoints(self):
        frame_copy = numpy.array(self.frame[:,:,0])
        frame_copy = cv2.medianBlur(frame_copy, Application.BLUR_FACTOR)
        cv2.filter2D(frame_copy, -1, Application.KERNEL, frame_copy)
        frame_copy = cv2.medianBlur(frame_copy, Application.BLUR_FACTOR)
        thresh = cv2.threshold(frame_copy, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        contours = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]

        contours = sorted(contours, key = lambda x: cv2.arcLength(x, True), reverse=True)
        points = []
        frame_copy = cv2.cvtColor(frame_copy, cv2.COLOR_GRAY2BGR)

        for c in contours:
            epsilon = 0.01 * cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, epsilon, True)
            mask = numpy.zeros_like(frame_copy[:, :, 0])
            cv2.drawContours(mask, [approx], -1, 255, -1)
            mean = cv2.mean(frame_copy, mask=mask)
            if (mean[0] > Application.MARKER_THRESHOLD):
                m = cv2.moments(approx)
                try:
                    x = int(m["m10"] / m["m00"]) 
                    y = int(m["m01"] / m["m00"]) 
                    points.append((x, y))
                except:
                    return 0
            if self.calibrating_state and len(points) >= 3:
               break

        if len(points) < 3:
            return 0

        # Point tracking
        if not self.calibrating_state:
            distance_f = lambda p1, p2: numpy.sqrt(numpy.dot(numpy.subtract(p1, p2), numpy.subtract(p1, p2)))
            
            costs = [[], [], []]
            for i in range(3):
                for j in range(len(points)):
                    costs[i].append((j, distance_f(self.prev_points[i], points[j])))
                costs[i].sort(key = lambda x: x[1])

            solutions = []
            for k0 in range(3):
                for k1 in range(3):
                    for k2 in range(3):
                        if ((costs[0][k0][0] != costs[1][k1][0]) and
                            (costs[1][k1][0] != costs[2][k2][0]) and
                            (costs[2][k2][0] != costs[0][k0][0])):
                           solutions.append((costs[0][k0][0], costs[1][k1][0], costs[2][k2][0]))

            def cost_f(x):
                result = 0
                for i in range(3):
                    j = 0
                    while costs[i][j][0] != x[i]:
                        j += 1
                    result += costs[i][j][1]
                return result
                    
            best_index = 0
            best_cost = cost_f(solutions[best_index])
            for i in range(len(solutions)):
                current_cost = cost_f(solutions[i])
                if current_cost < best_cost:
                    best_index = i
                    best_cost = current_cost

            new_points = [[], [], []]
            for i in range(3):
                new_points[i] = points[solutions[best_index][i]]
            points = new_points

        if self.calibrating_state:
            min_y = 0
            for i in range(1, 3):
                if points[i][1] < points[min_y][1]:
                    min_y = i
            self.mid_point = min_y
            
        self.calibrating_state = False
        self.prev_points = points
        return 1
    
    def __findAngle(self):
        points = self.prev_points.copy()
        mid = self.prev_points[self.mid_point]
        points.remove(mid)
        vector = []
        vector.append(tuple(numpy.subtract(mid, points[0])))
        vector.append(tuple(numpy.subtract(mid, points[1])))
        vector.append(tuple(numpy.subtract(points[0], points[1])))
        mag = []
        for v in vector:
            mag.append(numpy.dot(v, v))
        try:
            self.angle = numpy.arccos((mag[0] + mag[1] - mag[2]) / (2*numpy.sqrt(mag[0]*mag[1])))
            self.angle = int((self.angle * 180 / numpy.pi))
        except:
            self.angle = -1

    def __getFrame(self):
        if self.input_source == Application.INPUT_TYPE.Camera:
            self.success, self.frame = self.video_capture.read()

        if self.input_source == Application.INPUT_TYPE.CSV:
            try:
                data = next(self.input_reader)
                self.frame = cv2.imread(data[8])
                self.success = 1
            except StopIteration:
                self.success = 0

    def __storeFrame(self, id, prefix):
        name = f"{self.output_file_template}_{prefix}_{id}.png"
        cv2.imwrite(name, self.frame)
        self.csv_queue.append(name)

    def __storeCSV(self):
        data = [number for point in self.prev_points for number in point] + [self.mid_point+1] + [self.angle] + self.csv_queue
        self.output_writer.writerow(data)
        self.csv_queue.clear()
    
    def __drawWindow(self, recording=False):
        window_id = str(time.clock_gettime(time.CLOCK_REALTIME)).replace('.', '').ljust(17, '0')
        if self.output_mode:
            self.__storeFrame(window_id, 'orig')
            pass
        if self.points_success:
            for i in range(len(self.prev_points)):
                width = Application.MARKER_CENTER_WIDTH if i == self.mid_point else Application.MARKER_WIDTH
                cv2.circle(self.frame, self.prev_points[i], width, Application.MARKER_COLORS[i], -1)
            for i in range(len(self.prev_points)):
                cv2.line(self.frame, self.prev_points[self.mid_point], self.prev_points[i], Application.LINE_COLOR, Application.LINE_WIDTH)
            print(self.angle)
        cv2.imshow(self.name, self.frame)
        if self.output_mode:
            self.__storeFrame(window_id, 'marked')
            self.__storeCSV()
            
    def __keyboardResponse(self):
        k = cv2.pollKey()
        if (k == 8): # backspace
            app.success = False
        if (k == 13): # enter
            self.calibrating_state = True
            self.prev_points = [(0, 0), (0, 0), (0, 0)]
            # self.mid_point = (self.mid_point + 1) % 3
        
################################################################################

app = Application("Marker tracking")
# app.setCamera("/dev/video2")
app.output_mode = False
# app.setOutputFile("./recordings/test4")
app.setInputFile("./recordings/test4")
while app.success:
    app.run()
app.close()
    
