# Actuator Bending Angle

The final version of the application is `actuator_aruco.py`. It uses a robust ArUco marker detection routine implemented in OpenCV to calibrate the image and calculate the actuator's angle.

## Command line arguments
The program can be called with multiple command line options.
- `-c` or `--camera`. A camera source is selected as video input. The argument is either an index (e.g. `0`, `1`, `2`, etc.) or a path to device (e.g. `/dev/video0`).
- `-i` or `--input`. A recorded file is selected as video input.
- `-o` or `--output`. Indicates path where the recording will be saved.
- `-d` or `--delay`. Useful when a recorded video is played and a slower frame rate is desired. Delay is specified in seconds, although the actual delay between the frames also varies depending on the image complexity.
**Note:** `--camera` and `--input` cannot be specified together.

## Application class interface
- Constructor. Takes a string as argument, which will be the application's window name.
- `setCamera(source)`. Selects a camera source to be used as input. For example, `setCamera(0)` selects the first camera the computer connected to during the boot.
- `setInputFile(path)`. Selects a directory of a recording to be used as input. The directory must contain a CSV file and frame images.
- `setOutputFile(path)`. Selects a destination directory for recording.
- `run()`. Used in the application's while loop to fetch and process frames, draw window and save data.
- `close()`. Used in the end of program to close window, camera and files.
- `output_mode` is a boolean which indicates whether the recording is active and is disabled by default. It can be used to start and pause the recording when needed. When *R* is pressed, this flag is toggled.
- `success` is a flag intended to be used as condition of the application's while loop. When camera gets disconnected or *Backspace* is pressed, the flag becomes `False`.

### Example of using camera and recording:
```
app = Application("Marker tracking")
app.setCamera("/dev/video2")
app.output_mode = True
app.setOutputFile("./recordings/test")
while app.success:
	app.run()
app.close()
```
	
### Example of replaying a recording
```
app = Application("Marker tracking")
app.setInputFile("./recordings/test")
while app.success:
    app.run()
	time.sleep(0.1)
app.close()
```

## Recorded file structure
When `Application.setOutputFile(path)` is called, a directory is created for storing original frames, processed frames, and a CSV file. The CSV file's format is as follows:

|x1|y1|x2|y2|x3|y3|vertex|angle|orig\_path|marked\_path|
|---|---|---|---|---|---|---|---|---|---|
|531|222|314|250|380|214|2|21|./test/test\_orig\_1.png|./test/test\_marked\_1.png|
|555|215|332|236|401|202|2|20|./test/test\_orig\_1.png|./test/test\_marked\_2.png|

where `xn` and `yn` are coordinates of the *nth* point, `vertex` is the index of the point where the angle is measured at, angle field is for angle in degrees, orig\_path is the path to the original frame captured by the camera, and marked\_path is the path to the frame which was processed.
The CSV file can contain a comment line like this:
```
# c pressed
```
which means that the C key was pressed, making the program to calculate a new perspective transform.

## Processing a single frame
The `run()` function, which is executed in an infinite loop, consists of several calls:
```
self.__getFrame()
if self.success:
	self.__findAngle()
	self.__drawWindow()
self.__keyboardResponse()
```
Here is a description of the private methods:
- `__getFrame()`. Depending on the input type, that is either live video capture or replaying a recording, new frame is obtained and stored inside the object instance.
- `__findAngle()`. The current frame is processed by finding ArUco markers, calculating their center points, correcting the points using perspective transformation, and finally calculating the angle using the law of cosines.
- `__perspectiveCalibration()`. Finds 4 ArUco markers for calibration and calculated the perspective transform matrix. The 4 markers, in reality, form a square, and the points can be precisely corrected with this knowledge.
- `__drawWindow()`. All changes to the frame are done in this function. Before drawing anything, the frame is saved as *original* if the recording in on. Then, although computationally expensive and unnecessary, perspective tranformation is applied to the whole frame for the demonstration purposes. If all three markers of the actuator are found, they are marked with points and connected with lines. The frame is extended on the bottom to provide information about the angle and recording status.
- `__keyboardResponse()`. The application uses three keys. *Backspace* is for closing the window. *C* is for perspective calibration. *R* is for toggling the recording.

## ArUco markers in use
Marker for the tips of actuator (ArUco 4x4, id 8, 2 pc.):
n![ArUco 4x4 8](./readme_img/aruco_4x4_8.png)

Marker for the vertex of actuator (ArUco 4x4, id 9, 1 pc.):
![ArUco 4x4 9](./readme_img/aruco_4x4_9.png)

Marker for perpsective calibration (ArUco 4x4, id 42, 4 pc.):
![ArUco 4x4 42](./readme_img/aruco_4x4_42.png)


## Other implementations
The first implementations have the same class structure, functions and CSV format, but are lacking command line arguments.
- `actuator_points.py`. Analyzes the frames from the blue channel, because the actuator is yellow and it is distinguishable the most in this channel. The algorithm searches the white color surrounded by black. Once the points are found, they are constantly tracked until a recalibration is forced. This approach is robust because finding the white color is easy and there are almost no false positive detections thanks to tracking. The accuracy of the results heavily depends on the angle between the camera and the actuator's plane.
- `actuator_pespective.py`. This was the first try to improve the accuracy caused by perspective distorsions. The perspective transform matrix is calculated from the tiny square marker located at the vertex. The marker detection idea is the same as in the previous implementation. While the measurement was improved for extreme angles between the camera and the actuator, due to the size of the marker the are large errors. Angle measured in two similar frames can significantly vary.
