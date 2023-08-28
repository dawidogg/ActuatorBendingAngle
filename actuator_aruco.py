import cv2
import numpy
import enum
import time
import random
import csv
import os

class Application:
    class INPUT_TYPE(enum.Enum):
        Undefined = -1
        Camera = 0
        CSV = 1          

    def __init__(self, name):
        self.name = name
        cv2.namedWindow(self.name)
        self.angle = 0
        self.points = [(0, 0)]*3
        self.margins = [(0, 0)]*3
        self.output_mode = False
        self.csv_queue = []
        self.input_source = Application.INPUT_TYPE.Undefined
        self.success = 1

    def setCamera(self, source):
        self.input_source = Application.INPUT_TYPE.Camera
        self.video_capture = cv2.VideoCapture(source)

    def setInputFile(self, source):
        self.input_source = Application.INPUT_TYPE.CSV
        self.input_file_template = source + '/' + source[source.rfind('/')+1 :]
        self.input_file_csv = open(self.input_file_template+".csv", mode="r")
        self.input_reader = csv.reader(self.input_file_csv)
        next(self.input_reader)
        
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
        head = ["x1", "y1", "x2", "y2", "x3", "y3", "angle","orig_path", "marked_path"]
        self.output_writer.writerow(head)
        self.output_mode = True
        
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
        data = [number for point in self.points for number in point] + [self.angle] + self.csv_queue
        self.output_writer.writerow(data)
        self.csv_queue.clear()
        

    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    parameters =  cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(dictionary, parameters)

    def __findAngle(self):
        markerCorners, markerIds, _ = Application.detector.detectMarkers(self.frame)
        markers = [] # [id, coordinate] 
        for i in range(len(markerCorners)):
            if markerIds[i][0] == 42:
                continue
            center = sum(markerCorners[i][0])/4
            center = [int(center[0]), int(center[1])]
            markers.append([markerIds[i][0], center])
        markers.sort(key = lambda x: x[0])

        if len(markers) >= 3 and not(markers[0][0] == markers[1][0] == 8 and markers[2][0] == 9):
            self.angle = -1
            return
        
        boundaries = numpy.float32([
            [0, 0],
            [0, self.frame.shape[1]],
            [self.frame.shape[0], self.frame.shape[1]],
            [self.frame.shape[0], 0],
        ])

        
        
    def __drawWindow(self):
        pass

    def __keyboardResponse(self):
        k = cv2.pollKey()
        if (k == 8): # backspace
            app.success = False
        
app = Application("name")
app.setCamera("/dev/video2")
while app.success:
    app.run()
app.close()
