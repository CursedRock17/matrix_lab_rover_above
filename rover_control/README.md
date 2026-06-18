# Rover Control
In this file lies all of the higher level control code to drive a given rover around

## Setup 
The setup is quite barebones, but given you're already in a conda environment, source that environment and install the necessary packages:

```bash
export ENV_NAME=rover_high_level
conda activate $ENV_NAME
python3 -m pip install pynput
```

## Simple API
The easiest way to drive the rover: create one `Rover` and call high-level methods. No control loops, no PID, no estimator wiring - all of that lives inside these methods. See [examples/simple_api_demo.py](examples/simple_api_demo.py).

```python
from rover_control.rover import Rover

rover = Rover(show_camera=True)        # show_camera=True pops up what the camera sees
try:
    rover.run_maze([0, 1])             # drive to ArUco tag 0, then tag 1
    rover.follow_object("bottle")      # find a COCO object and drive up to it
finally:
    rover.stop()
    rover.close()                      # shuts down the background camera reader
```

| Method | What it does |
|--------|--------------|
| `run_maze([0, 1, 2])` | Drive to a list of ArUco tags in order. |
| `drive_to_tag(0)` | Search for one ArUco tag, center on it, drive up to ~0.25 m away. |
| `follow_object("bottle")` | Find a COCO object (YOLO), center on it, drive up to it. |
| `run_object_maze(["bottle", "cup"])` | Drive to a list of COCO objects in order. |
| `forward(0.5)` | Drive straight 0.5 m on a trapezoidal speed curve (negative = backward). |
| `turn(-90)` | Spin in place; **positive = right**, negative = left (degrees). |
| `see_tag(0)` | One stop-and-stare reading: `{"position": [x, y, z], "bearing": deg, "distance": m}` or `None`. |
| `stop()` / `close()` | Halt the rover / shut down the camera reader. |

**Coordinate frame:** `position` is `[X, Y, Z]` in meters, as seen from the rover - **+X right, +Y up, +Z forward**.

**Good to know:**
- `forward()` and `turn()` are **open-loop** (timed), so distance/angle drift a little; `drive_to_tag`/`follow_object` re-measure visually, so they self-correct.
- Tag/object readings are taken **while stopped** (the rover turns, halts, takes several agreeing frames, then decides) to beat the camera's 1-2 frame lag - reliable but not fast. `follow_object` is slowest (~1 s/frame for the depth step).
- Every motion method **stops the rover on Ctrl-C** or any error, so it can't run away.
- The PID-based and per-frame examples below are the "under-the-hood" versions for students who want to see or extend the internals.

## Example Executables

------------------------------------------------------------------------------------------------------------------------------------------------
| Executable | Purpose |
|------------|---------|
| [Simple API Demo](examples/simple_api_demo.py) | The whole student program in a few lines: create a `Rover` and call `run_maze` / `drive_to_tag` / `follow_object`. |
| [Manual Control](examples/manual_control.py) | Allows you to drive the physical rover with your keyboard, scaling the speed to your desire. |
| [ArUco Pose Movement](examples/aruco_pose_movement.py) | Allows the rover to autonomouslu navigate to an ArUco tag and stop a set distance away.|
| [ArUco Tag Tracker](examples/aruco_tag_tracker.py) | Keeps tracking a moving ArUco tag, holding a set standoff distance and spinning to find it if lost. |
| [YOLO Object Movement](examples/yolo_object_movement.py) | Navigates the rover toward a named COCO object using YOLO 3D pose, stopping a set distance away. |
| [ArUco Maze Runner](examples/aruco_maze_runner.py) | Drives the rover through a list of ArUco tags in order, spinning in place to search for each next tag. |
| [ArUco Maze Runner (Trapezoid)](examples/aruco_maze_runner_trapezoid.py) | Same maze, but looks once per tag then drives a planned trapezoidal speed curve instead of a continuous PID. |
| [Encoder Readout](examples/encoder_readout.py) | Polls the rover for its wheel encoder counts over UDP (the `e` command) and prints the replies. |
| [Local Camera + YOLO Estimation](examples/simple_yolo_distance_estimation.py) | Metric depth estimation using Depth-Anything-V3 from a YOLO bounding box for any given object |
------------------------------------------------------------------------------------------------------------------------------------------------
