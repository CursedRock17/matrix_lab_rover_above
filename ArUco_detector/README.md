# ArUco Detector
This folder contains all of the information for writing the ArUco marker pose estimator, which returns a pose in a standard format.
ArUco markers are *fiducial markers* which are made up of evenly sized squares which are binary in nature, being filled in either white or black. These squares can be formulated into a variety of patterns, established in the foundational paper released in 2014, known as [Automatic generation and detection of highly reliable fiducial markers under occlusion](https://www.sciencedirect.com/science/article/abs/pii/S0031320314000235).
We need 3 distinct pieces of information for the marker to provide us any use:
- The standard square side length (in meters)
- The dictionary the marker is from
- The ID of the marker within that dictionary

From this information, we can extract the position (X, Y, Z) in meters and orientation (yaw) of the marker **as seen from the rover** — the camera is the origin, not the tag. This right-handed coordinate frame presents:
- Positive X-Axis: Right
- Positive Y-Axis: Up
- Positive Z-Axis: Forward

(OpenCV natively returns this vector with +Y pointing *down*; the `ArucoPoseEstimator` flips it so +Y is up to match the frame above.)

For a deeper expansion of knowledge, it's best to fully understand [coordinate systems and reference frames](https://eng.libretexts.org/Bookshelves/Mechanical_Engineering/Introduction_to_Autonomous_Robots_(Correll)/03%3A_Forward_and_Inverse_Kinematics/3.01%3A_Coordinate_Systems_and_Frames_of_Reference).
To generate different markers, I recommend [Oleg Kalachev's Generator](https://chev.me/arucogen/)

## Calibrating your camera
In order to get meaningful pose estimates from your ArUco marker, you must have a calibrated camera. A calibration script and example `.yaml` output file are located in the [calibration](calibration/) folder.
This tutorial is "forked" from an old [automaticaddison](https://automaticaddison.com/how-to-perform-pose-estimation-using-an-aruco-marker/) guide; all credit is due to him (his content is peak).

1) Print out the attached [pattern.png](calibration/pattern.png) on typical A4 printer paper, horizontally, such that the checkerboard pattern fills out most of the page.
2) Take a plethora of photos (saved in `.jpg` format in the `calibration/` directory) so that the whole checkerboard is seen clearly with low background noise, get as many angles and heights as possible, 10 is the minimum; the more, the better.
3) Run the [calibration script](calibration/coolest_calibrator.py) which will output a calibration matrix and distortion coefficients vector that you can use to set up the ArUco class.


## ArUco Pose Estimator Class — Quick Integration Guide

This class wraps ArUco marker detection, pose estimation, and smoothing into a reusable interface that can be dropped into any existing control loop.

---

### 1. Initialization

Create the estimator once, outside your main loop:

```python
estimator = ArucoPoseEstimator(
    camera_matrix=camera_matrix,
    dist_coeffs=dist_coeffs,
    marker_length_m=0.10,
    http_addr="http://192.168.50.123:80/capture",
    verbose=True  # set False if you only want data
)
```

### 2. Use Inside a Control Loop
Call `process()` once per iteration. It returns the freshest frame from the background reader **without blocking**, so pace your own loop (a short sleep) instead of spinning the CPU.

```python
import time

while True:
    frame, poses = estimator.process()
    if poses:
        print(poses)

    # Optional display if verbose=True
    if frame is not None:
        cv2.imshow("Aruco", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

    time.sleep(0.05)  # ~20 Hz - process() no longer blocks, so pace the loop yourself
```

### 3. Query for a Marker Position
You can directly query a marker without processing the full dictionary:

```python
pos = estimator.get_position(marker_id=1)
print(pos)  # [x, y, z] or None if not seen
```

-----------------------------------------------------------

## Troubleshooting
**Can't find your camera stream**
Each rover is set up with a written IP address in which the camera is in the 100s, the rover is in the 200s (example: 192.168.50.123 Camera, 192.168.50.223 Rover)

**Check image**
Puts up a webpage at the address of the camera with port 80

**Extensions**
- "/capture" : Grab JPEG still images more easily.
- "/stream"  : Stream MJPEG images. *warning* camera may overheat

