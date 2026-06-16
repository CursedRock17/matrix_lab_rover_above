# YOLO Agent
This folder will contain the running code for getting YOLO models to run with your rover.
YOLO stands for **Y**ou **O**nly **L**ook **O**nce, you can see the main page [here](https://docs.ultralytics.com/#where-to-start). These are Convolutional Neural Networks (CNNs) that implement object detection by comparing close groups of pixels (kernels), computing differences between these pixels and sending these differences through multiple layers of nodes. The underlying dataset is called COCO (Common Objects in Context) and has millions of different objects that were separated out by hand and labelled with a given name, models like YOLO are trained on these massive datasets which is how the neural network can change outputs to match the object you desire.

## Set up
You should've done this in the main setup, but make sure you've installed ultralytics:
```bash
python3 -m pip install ultralytics
```

### Models
You can technically use whatever of the various [YOLO Models](https://huggingface.co/Ultralytics/models) that you want, but we recommend sticking to:
- [YOLOv8n](https://huggingface.co/Ultralytics/YOLOv8#models) as it will be super fast for your cheap camera. Download the `.pt` file [here](https://huggingface.co/Ultralytics/YOLOv8/tree/main)

## Getting Started
The best way to get started is by running the [local camera example](yolov8n_local_example.py) which does basic object detection on your own camera. All of the detection logic lives in the [YOLOExtractor](YOLO_extractor.py) class, which you can import and reuse anywhere (the ArUco follower style control loops included).

## Example Executables

| Executable | Purpose |
|------------|---------|
| [YOLO Local Camera](yolov8n_local_example.py) | Runs YOLOv8n object detection live on your laptop's own camera (video port 0). |
| [YOLO ESP32 Camera](yolov8n_esp32_example.py) | Runs YOLOv8n object detection on JPEG stills polled from the rover's ESP32 camera. |
| [YOLO 3D Pose](yolov8n_pose_example.py) | Adds a real-world (X, Y, Z) position in meters to every detection using a monocular depth model. |

## Getting a 3D Pose for Any Object
The [YOLOPoseEstimator](yolo_pose_estimator.py) class pairs YOLO (what + where in the image) with a monocular depth model ([Depth Anything V2 metric](https://huggingface.co/depth-anything/Depth-Anything-V2-Metric-Indoor-Small-hf), downloaded automatically on first use) to give each detection a real-world position — the same (X right, Y down, Z forward) pose the ArUco tracker reports, but for any COCO object with no tag. The depth pass is the slow part (~1 s/frame on a laptop CPU), so this runs at a couple frames per second rather than the detector's ~9-17 Hz.

---

## Depth Anything 3 GPU Server

If you have access to a desktop with an NVIDIA GPU on the same network, you can offload all depth inference to it. The rover laptop sends one JPEG frame over HTTP and gets a full float32 depth map back — matching the camera's 15 FPS rather than the laptop's ~2 FPS.

**Architecture:**
```
ESP32 camera  →  rover laptop  →(HTTP POST /depth)→  desktop GPU
                     ↑                                      |
              YOLO detection                     Depth Anything 3 Large
                     ↑                                      |
              (X, Y, Z) pose  ←─── float32 depth map ←──────┘
```

### Step 1 — Verify the model name

Before setting up the desktop, confirm the Depth Anything V3 Large model ID on HuggingFace:

> **[https://huggingface.co/depth-anything](https://huggingface.co/depth-anything)**

The server is configured with `MODEL_ID = "depth-anything/Depth-Anything-V3-Large-hf"` at the top of [depth_server.py](depth_server.py). Update this string if the published model ID differs.

### Step 2 — Desktop setup (one-time)

#### 2a. Install PyTorch with CUDA

**Do this first, before the requirements file.** The correct index URL depends on your CUDA version.

Check your driver-supported CUDA version:
```bash
nvidia-smi
```
Look for `CUDA Version: XX.X` in the top-right of the output.

Then install PyTorch with the matching CUDA build. For **CUDA 12.6** (RTX 50-series / Blackwell requires ≥ 12.6):
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126
```
For **CUDA 12.4** (RTX 40-series and older):
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
```

> **RTX 50-series (5060 Ti, 5070, 5080, 5090) note:** These are Blackwell GPUs (SM 12.0) and require **PyTorch 2.6 or newer** with a CUDA 12.6 build. Older PyTorch releases will not see the GPU. Confirm with `python -c "import torch; print(torch.__version__, torch.cuda.get_device_name(0))"`.

#### 2b. Install the server dependencies

```bash
cd YOLO_agent
pip install -r requirements_depth_server.txt
```

#### 2c. Download the model

The model downloads automatically on the first server start. To pre-download it so the server starts faster (recommended):
```bash
huggingface-cli download depth-anything/Depth-Anything-V3-Large-hf
```
This caches the weights in `~/.cache/huggingface/hub/`. The model is large (hundreds of MB); download it once over ethernet, not over BaleNet WiFi.

### Step 3 — Start the server

On the desktop, run:
```bash
python YOLO_agent/depth_server.py
```
The server binds to all interfaces on **port 5000** by default and accepts up to **20 queued requests** — enough headroom for a full class of 15 rovers bunching up simultaneously. You will see the GPU name and "Depth server ready" once it finishes loading (~30–60 s first time, faster after caching).

```
Loading depth-anything/Depth-Anything-V3-Large-hf onto NVIDIA GeForce RTX 5060 Ti ...
Model loaded in 12.3s
Depth server ready — listening for JPEG frames
```

Optional flags:
```bash
python YOLO_agent/depth_server.py --host 0.0.0.0 --port 5000
```

#### Network check

The desktop and rover laptops must be on the same network (BaleNet, or the same travel router). Check that the desktop's firewall allows inbound connections on port 5000. Find the desktop's IP with:
```bash
ip addr   # Linux
ipconfig  # Windows
```

> **Travel router AP isolation:** Some travel routers block device-to-device traffic by default. If laptops cannot reach the desktop, look for an "AP isolation" or "client isolation" setting in the router admin page and disable it.

### Step 4 — Test the connection from a laptop

Before integrating with the rover code, confirm the round-trip works:
```bash
python YOLO_agent/depth_client.py --server http://<DESKTOP_IP>:5000 --image YOLO_agent/esp32_yolo_bottle.png
```
You should see the round-trip time and a side-by-side window of the original image and its depth map (bright = far).

### Step 5 — Use the remote depth in your code

Pass `depth_server_url` when creating a `YOLOPoseEstimator` and the remote GPU is used automatically for all depth inference. No other code changes are needed:

```python
from YOLO_agent.yolo_pose_estimator import YOLOPoseEstimator

estimator = YOLOPoseEstimator(
    model_path="YOLO_agent/models/yolov8n.pt",
    depth_server_url="http://192.168.50.XXX:5000",   # desktop IP
)

# Everything else is identical — process() still returns (annotated, detections)
# with "position" and "distance" on each detection, now powered by DA3 on the GPU.
annotated, detections = estimator.process(frame)
```

Omit `depth_server_url` (or set it to `None`) to fall back to the local DA2 Small CPU model.

### A note on precision

The server loads the model with `torch_dtype=torch.float16`. This stores weights as 16-bit floats (half precision) rather than 32-bit — it is **not quantization**. Quantization would mean compressing weights to integers (int8/int4), which visibly degrades depth quality. Half-precision floating point has no meaningful accuracy impact for depth estimation and cuts GPU memory usage in half, which is why it is the standard way to run these models on any NVIDIA GPU.
