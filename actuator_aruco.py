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
        self.points = [[0, 0]]*3
        self.margins = [[0, 0]]*3
        self.output_mode = False
        self.csv_queue = []
        self.input_source = Application.INPUT_TYPE.Undefined
        self.success = 1
        self.loop = False
        self.perspectiveMatrix = numpy.zeros((3, 3), dtype=float)
        self.calibrated = False
        self.markers = []
        
    def setCamera(self, source):
        self.input_source = Application.INPUT_TYPE.Camera
        self.video_capture = cv2.VideoCapture(source)
        self.__getFrame()
        
    def setInputFile(self, source):
        self.input_file_path = source
        self.input_source = Application.INPUT_TYPE.CSV
        self.input_file_template = source + '/' + source[source.rfind('/')+1 :]
        self.input_file_csv = open(self.input_file_template+".csv", mode="r")
        self.input_reader = csv.reader(self.input_file_csv)
        next(self.input_reader)
        self.loop = True
        
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
        if self.success:
            self.__findAngle()
            self.__drawWindow()
        return self.__keyboardResponse()

    def __getFrame(self):
        if self.input_source == Application.INPUT_TYPE.Camera:
            self.success, self.frame = self.video_capture.read()
        if self.input_source == Application.INPUT_TYPE.CSV:
            try:
                data = next(self.input_reader)
                if data == ["# c pressed"]:
                    if not self.calibrated:
                        self.perspectiveCalibration()
                    else:
                        self.calibrated = False
                    data = next(self.input_reader)

                if os.path.isfile(data[8]):
                    self.frame = cv2.imread(data[8])
                    self.success = 1
                else:
                    self.success = 0
                    self.__getFrame()

            except StopIteration:
                if self.loop:
                    self.setInputFile(self.input_file_path)
                    self.calibrated = False
                    self.__getFrame()
                else:
                    self.success = 0
                
    def __storeFrame(self, id, prefix):
        name = f"{self.output_file_template}_{prefix}_{id}.png"
        cv2.imwrite(name, self.frame)
        self.csv_queue.append(name)

    def __storeCSV(self):
        data = [number for point in self.markers for number in point] + [3] + [self.angle] + self.csv_queue
        self.output_writer.writerow(data)
        self.csv_queue.clear()
        
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    parameters =  cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(dictionary, parameters)
    
    def perspectiveCalibration(self):
        markerCorners, markerIds, _ = Application.detector.detectMarkers(self.frame)
        markers = []
        for i in range(len(markerCorners)):
            if markerIds[i][0] == 42:
                center = sum(markerCorners[i][0])/4
                markers.append(center)
        markers.sort(key = lambda x: x[0]*1000+x[1], reverse=True)
        
        if len(markers) != 4: return -1

        markers = numpy.float32(markers)

        boundaries = numpy.float32([
            [self.frame.shape[1], self.frame.shape[1]],
            [self.frame.shape[1], 0],
            [0, 0],
            [0, self.frame.shape[1]],
        ])

        self.perspectiveMatrix = cv2.getPerspectiveTransform(markers, boundaries)
        self.calibrated = True
        print(self.perspectiveMatrix)

    def __findAngle(self):
        try:
            markerCorners, markerIds, _ = Application.detector.detectMarkers(self.frame)
        except:
            return
        markers = [] # [id, coordinate] 
        for i in range(len(markerCorners)):
            if not (markerIds[i][0] == 8 or markerIds[i][0] == 9):
                continue
            center = sum(markerCorners[i][0])/4
            center = [int(center[0]), int(center[1])]
            if (markerIds[i][0] == 8):
                markers.insert(0, center)
            if (markerIds[i][0] == 9):
                markers.append(center)

        if len(markers) != 3: return -1

        if self.calibrated:
            for i in range(len(markers)):
                point = cv2.perspectiveTransform(numpy.float32(markers[i]).reshape(-1, 1, 2), self.perspectiveMatrix)
                point = [int(p) for p in point[0][0]]
                markers[i] = point
        
        vector = []
        vector.append(numpy.subtract(markers[2], markers[0]))
        vector.append(numpy.subtract(markers[2], markers[1]))
        vector.append(numpy.subtract(markers[0], markers[1]))
        mag = [numpy.dot(v, v) for v in vector]

        try:
            self.angle = numpy.arccos((mag[0] + mag[1] - mag[2]) / (2*numpy.sqrt(mag[0]*mag[1])))
            self.angle = int((self.angle * 180 / numpy.pi))
        except:
            self.angle = -1
        self.markers = markers
        print(f"Angle: {self.angle}")
        

    def __drawWindow(self):
        window_id = str(time.clock_gettime(time.CLOCK_REALTIME)).replace('.', '').ljust(17, '0')
        if self.output_mode:
            self.__storeFrame(window_id, 'orig')

        if self.calibrated:
            self.frame = cv2.warpPerspective(self.frame, self.perspectiveMatrix, (self.frame.shape[1], self.frame.shape[1]))
            if len(self.markers) == 3:
                cv2.line(self.frame, self.markers[2], self.markers[0], (0, 0, 0), 4)
                cv2.line(self.frame, self.markers[2], self.markers[1], (0, 0, 0), 4)
                cv2.circle(self.frame, self.markers[0], 5, (0, 0, 255), -1)
                cv2.circle(self.frame, self.markers[1], 5, (0, 0, 255), -1)
                cv2.circle(self.frame, self.markers[2], 5, (255, 0, 0), -1)
                
        cv2.imshow(self.name, self.frame)

        if self.output_mode:
            self.__storeFrame(window_id, 'marked')
            self.__storeCSV()

    def __keyboardResponse(self):
        k = cv2.pollKey()
        if (k == 8): # backspace - close
            app.success = False
        if (k == 99): # c - calibrate
            if not self.calibrated:
                self.perspectiveCalibration()
            else:
                self.calibrated = False
            if self.output_mode:
                self.output_writer.writerow(["# c pressed"])
        if (k == 114): # r - toggle record
            pass
            
app = Application("Aruco markers")
# app.setInputFile("./recordings/aruco_test")
app.setCamera("/dev/video2")
# app.setOutputFile("./recordings/aruco_test2")
while app.success:
    app.run()
app.close()