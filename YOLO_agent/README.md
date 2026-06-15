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
