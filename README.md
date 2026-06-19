# Matrix Lab Rover — High Level
This repository contains the higher-level AI agent code for the STEM Rovers: object detection, ArUco pose estimation, LLM integration, and the control loops that tie them together into autonomous behaviours.
The intent is to elevate the basic differential drive rover platform we're currently control with closed loop techniques, with modern neural network, higher level algorithms.

## Installation

### Prerequisites
1. Install [Python3](https://www.python.org/downloads/)
2. Install [Git](https://git-scm.com/install/) on your platform
3. Install [Miniconda](https://www.anaconda.com/docs/getting-started/miniconda/main) on your desired platform:
    - [Windows](https://www.anaconda.com/docs/getting-started/miniconda/install/windows-cli-install)
    - [MacOS](https://www.anaconda.com/docs/getting-started/miniconda/install/mac-cli-install)
    - [Linux](https://www.anaconda.com/docs/getting-started/miniconda/install/linux-install)
4. Clone this repository locally:

    ```bash
    git clone https://github.com/CursedRock17/matrix_lab_rover_above.git
    ```

### Repository Setup

1) Create a conda environment:
    ```bash
    conda create -n rover_high_level python=3.10
    ```

2) Activate the environment and install this project (run from this folder):
    ```bash
    conda activate rover_high_level
    # On a machine without an NVIDIA GPU, grab the small CPU-only torch first (saves ~6 GB)
    # python3 -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
    python3 -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
    python3 -m pip install -e .
    ```

This installs the project's folders (`ArUco_detector`, `YOLO_agent`, `LLM_hybrid`, `rover_control`) as importable Python packages, along with their dependencies (`opencv-contrib-python`, `ultralytics`, `numpy`, `pynput`, `ollama`, `transformers`, `pillow`) listed in `pyproject.toml` and `requirements.txt` — no `PYTHONPATH` setup needed.

3) (Only for the `LLM_hybrid` examples) Install and start the local Ollama server — see [LLM_hybrid/README.md](LLM_hybrid/README.md) for the two-command setup.

---

## Project Structure

```
matrix_lab_rover_above/
├── ArUco_detector/          OpenCV-based ArUco marker detector. Reads a JPEG still from the
│                            ESP32 camera, finds any markers from a chosen dictionary, and
│                            returns each tag's (X, Y, Z) pose in meters.
├── YOLO_agent/              YOLOv8n object detector for COCO classes, plus a monocular depth
│                            estimator that pairs YOLO bounding boxes with Depth Anything V3
│                            to produce real-world (X, Y, Z) positions with no tag required.
├── LLM_hybrid/              Ollama integration for local vision LLMs. Can describe what the
│                            camera sees and output rover velocity commands as structured JSON.
├── depth_anything_server/   FastAPI server that offloads Depth Anything V3 inference to a
│                            shared desktop GPU. Rover laptops send a JPEG frame over HTTP and
│                            receive a full float32 depth map in return.
└── rover_control/           Rover base class and all runnable examples. Sends motor commands
        └── examples/        over UDP at 10 Hz and reads encoder counts over the same link.
                             All other folders are imported here — this is where students run code.
```

---

## Examples

| Example | Folder | What it does |
|---------|--------|-------------|
| ArUco Pose Movement | [rover_control/examples/](rover_control/examples/) | Finds an ArUco tag, centers on it, and drives to ~0.25 m away. |
| ArUco Maze Runner | [rover_control/examples/](rover_control/examples/) | Navigates a sequence of ArUco tags in order using a continuous PID approach. |
| ArUco Maze Runner (Trapezoid) | [rover_control/examples/](rover_control/examples/) | Same maze, but uses a planned trapezoidal speed curve — more reliable in poor lighting. |
| ArUco Tag Tracker | [rover_control/examples/](rover_control/examples/) | Keeps a moving ArUco tag in frame at a fixed standoff distance, spinning to find it if lost. |
| YOLO Object Detection | [YOLO_agent/](YOLO_agent/) | Runs YOLOv8n on the laptop camera or ESP32 camera and returns detection dictionaries. |
| YOLO 3D Pose | [YOLO_agent/](YOLO_agent/) | Pairs YOLO detections with a depth model to give each object a real-world (X, Y, Z) position. |
| YOLO Object Navigation | [rover_control/examples/](rover_control/examples/) | Drives the rover toward a named COCO object using its YOLO 3D pose. |
| Depth Server | [depth_anything_server/](depth_anything_server/) | Offloads Depth Anything V3 inference to a desktop GPU; laptops send a JPEG and get a depth map back. |
| LLM Object Identification | [LLM_hybrid/](LLM_hybrid/) | Asks a local vision LLM what object is in frame and returns a structured JSON answer. |
| LLM Rover Driving | [LLM_hybrid/](LLM_hybrid/) | Proof of concept where the LLM watches the camera stream and outputs rover velocity commands. |
