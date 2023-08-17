# Actuator Bending Angle

## Calculating angle from the centers of markers
	The file `actuator_points.py` contains an implementation of tracking 3 markers, calculating the angle of the actuator, writing and reading `csv` files. It consists of a class `Application` with an example.
	
### Interface
	- Constructor. Takes a string as argument, which will be the application's window name.
	- `setCamera(source)`. Selects a camera source to be used as input. For example, `setCamera(0)` selects the first camera the computer connected to during the boot.
	- `setInputFile(source)`. Selects a directory of a recording to be used as input. The directory must contain a `csv` file and frame images.
	- `setOutputFile(source)`. Selects a destination directory for a recording.
	- `output_mode` is a boolean which, when `True`, allows recording. Can be used to start the recording and pause when needed.
	- `success` is a flag intended to be used as condition of the application's while loop. When camera gets disconnected, recorded video ends, or *Backspace* is pressed, the flag becomes `False`.
	- `run()`. Used in the application's while loop to fetch and process frames, draw window and save data.
	- `close()`. Used in the end of program to close window, camera and files.

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
app.output_mode = False
app.setInputFile("./recordings/test")
while app.success:
    app.run()
app.close()
```

### CSV structure
|x1|y1|x2|y2|x3|y3|vertex|angle|orig\_path|marked\_path|
-----------------------------------------------------
|531|222|314|250|380|214|2|21|./test/test\_orig\_1.png|./test/test\_marked\_1.png|
-----------------------------------------------------
|555|215|332|236|401|202|2|20|./test/test\_orig\_1.png|./test/test\_marked\_2.png|
-----------------------------------------------------
### Processing a single frame
	The `run()` function consists of several calls:
```
self.__getFrame()
self.points_success =  self.__findPoints()
if self.points_success:
	self.__findAngle()
self.__drawWindow()
return self.__keyboardResponse()
```


## Calculating angle using perspective transform
