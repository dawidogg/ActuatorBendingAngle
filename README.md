# Actuator Bending Angle

## Calculating angle from the centers of markers
The file `actuator_points.py` contains an implementation of tracking 3 markers, calculating the angle of the actuator, writing and reading `csv` files. It consists of a class `Application` with an example.

## Command line arguments
The program can be called with multiple command line options.
- `-c` or `--camera`. A camera source is selected as video input. The argument is either an index (e.g. `0`, `1`, `2`, etc.) or a path to device (e.g. `/dev/video0`).
- `-i` or `--input`. A recorded file is selected as video input.
- `-o` or `--output`. Indicates path where the recording will be saved.
- `-d` or `--delay`. Useful when a recorded video is played and a slower frame rate is desired. Delay is specified in seconds, although the actual delay between frames also varies depending on the image complexity.
**Note:** `--camera` and `--input` cannot be specified together.

## Application class interface
- Constructor. Takes a string as argument, which will be the application's window name.
- `setCamera(source)`. Selects a camera source to be used as input. For example, `setCamera(0)` selects the first camera the computer connected to during the boot.
- `setInputFile(path)`. Selects a directory of a recording to be used as input. The directory must contain a `csv` file and frame images.
- `setOutputFile(path)`. Selects a destination directory for recording.
- `run()`. Used in the application's while loop to fetch and process frames, draw window and save data.
- `close()`. Used in the end of program to close window, camera and files.
- `output_mode` is a boolean which indicates whether the recording is active and is disabled by default. It can be used to start and pause the recording when needed. When *R* is pressed, this flag is toggled.
- `success` is a flag intended to be used as condition of the application's while loop. When camera gets disconnected, recorded video ends, or *Backspace* is pressed, the flag becomes `False`.

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

### Recorded file structure
When `Application.setOutputFile(path)` is called, a directory is created for storing original frames, processed frames, and a CSV file. The CSV file's format is as follows:

|x1|y1|x2|y2|x3|y3|vertex|angle|orig\_path|marked\_path|
|---|---|---|---|---|---|---|---|---|---|
|531|222|314|250|380|214|2|21|./test/test\_orig\_1.png|./test/test\_marked\_1.png|
|555|215|332|236|401|202|2|20|./test/test\_orig\_1.png|./test/test\_marked\_2.png|

where `xn` and `yn` are coordinates of the *nth* point, `vertex` is 

### Processing a single frame
The `run()` function consists of several calls:
```
self.__getFrame()
if self.success:
	self.__findAngle()
	self.__drawWindow()
self.__keyboardResponse()
```
