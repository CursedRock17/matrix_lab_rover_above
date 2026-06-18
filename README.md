# Rover High Level
This folder will showcase all of the higher level, AI-agent code that we'll use with the STEM Rovers

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
- rover_high_level/
    - ArUco_detector/ : Provides simple OpenCV code that is able to read a still JPEG from a http address in the format (http://192.168.50.123:80/capture), look for ArUco tags with a given Dict and ID, then export the pose from that tag. Code is wrapped into an easily extendable class that can be distributed.
    - YOLO_agent/     : Provides simple Python code that uses YOLOv8n (downloaded locally) to recognize objects. It should also be written in an easily portable class for access in other classes.
    - LLM_hybrid/     : Provides ollama extension with the ollama API that can allow the downloading of a model to export context.
    - depth_anything_server/ : Provides a standard server/client interface such that the ESP32 Rovers can interact with a CUDA-Enabled workstation by sending image frames and receiving a metric depth map from Depth-Anything-V3
    - rover_control/  : Provides a rover class that sends UDP commands at a given command rate which communicates with the STEM Rover firmware. This class is where we can drive the physical rover and access peripheral information (encoder counts), this where actual high-level rover code is executed from, seen in one of the examples, ArUco_detector and other folders should integrate their applications here.
        - examples/   : All of the runnable high-level processes live here - the other folders only hold the distributed classes they build on.
```

---

## Examples
- ArUco Marker Pose Estimation : Extract OpenCV streamed camera data, find an ArUco marker with a certain dictionary ID, extract pose from it. Export that pose to a twist
- YOLO Object Detection : Run YOLOv8n on your laptop camera or the rover's ESP32 camera and get back simple detection dictionaries (see YOLO_agent/)
- YOLO 3D Pose : Add a real-world (X, Y, Z) position in meters to each YOLO detection with a monocular depth model (see YOLO_agent/)
- YOLO Object Navigation : Drive the rover toward a named COCO object using its YOLO 3D pose (see rover_control/examples/)
- ArUco Tag Tracking : Keep tracking a moving ArUco tag at a fixed standoff distance (see rover_control/examples/)
- LLM Object Identification : Ask a local vision LLM what object is in frame and get a structured JSON answer (see LLM_hybrid/)
- LLM Rover Driving : Proof of concept where the LLM looks for a target object in the camera stream and emits the rover's velocity JSON message (see LLM_hybrid/)
