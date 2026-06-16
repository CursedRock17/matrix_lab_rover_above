"""
Depth Anything 3 remote depth client.

Sends a single JPEG frame to the depth server running on the desktop GPU and returns
a float32 depth map (metric meters, H×W numpy array) — the same format and coordinate
convention that the local YOLOPoseEstimator uses, so it is a drop-in replacement.

Standalone demo usage:
    python depth_client.py --server http://192.168.50.XXX:5000 --image path/to/image.jpg

Programmatic usage (drop-in for local depth inference):
    from YOLO_agent.depth_client import DepthServerClient
    client = DepthServerClient("http://192.168.50.XXX:5000")
    depth = client.get_depth(frame)   # frame is a BGR numpy array, depth is float32 H×W meters
"""

import argparse
import time

import cv2
import numpy as np
import requests


class DepthServerClient:
    """
    Thin HTTP wrapper around the depth server running on the desktop GPU.

    get_depth(frame) mirrors the signature and return value of YOLOPoseEstimator._depth_map_meters()
    so the two are interchangeable in any control loop.
    """

    def __init__(self, server_url: str, timeout: float = 30.0):
        """
        server_url: base URL of the depth server, e.g. "http://192.168.50.XXX:5000"
        timeout:    how long to wait for a response before raising (seconds)
        """
        self.depth_url = server_url.rstrip("/") + "/depth"
        self.health_url = server_url.rstrip("/") + "/health"
        self.timeout = timeout
        self._session = requests.Session()

    def check_health(self) -> dict:
        """
        Returns the server's /health JSON.  Raises requests.ConnectionError if unreachable.
        """
        resp = self._session.get(self.health_url, timeout=5.0)
        resp.raise_for_status()
        return resp.json()

    def get_depth(self, frame: np.ndarray) -> np.ndarray:
        """
        Send one BGR frame to the depth server and return a float32 depth map in meters.

        The returned array is the same shape as the input frame (H×W) — it has already
        been resized to match, so you can index directly with pixel coordinates.
        """
        # Encode the frame as a JPEG to keep the payload small over WiFi
        ok, jpeg_buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
        if not ok:
            raise RuntimeError("cv2.imencode failed — is the frame a valid BGR image?")

        resp = self._session.post(
            self.depth_url,
            data=jpeg_buf.tobytes(),
            headers={"Content-Type": "image/jpeg"},
            timeout=self.timeout,
        )
        resp.raise_for_status()

        h = int(resp.headers["X-Depth-Height"])
        w = int(resp.headers["X-Depth-Width"])
        depth = np.frombuffer(resp.content, dtype=np.float32).reshape(h, w)

        # Resize to match the original frame dimensions so pixel lookups line up
        frame_h, frame_w = frame.shape[:2]
        if (h, w) != (frame_h, frame_w):
            depth = cv2.resize(depth, (frame_w, frame_h))

        return depth


def main():
    parser = argparse.ArgumentParser(description="Send one JPEG to the depth server and show the result")
    parser.add_argument("--server", required=True, help="Server base URL, e.g. http://192.168.50.XXX:5000")
    parser.add_argument("--image", default=None, help="Path to a JPEG file (omit to use the laptop camera)")
    args = parser.parse_args()

    client = DepthServerClient(args.server)

    # Confirm the server is alive before we send anything
    try:
        info = client.check_health()
        print(f"Server OK — model: {info['model']}, GPU: {info['gpu']}, queue: {info['queue_depth']}")
    except Exception as exc:
        print(f"Could not reach server at {args.server}: {exc}")
        return

    # Grab one frame from a file or the laptop camera
    if args.image:
        frame = cv2.imread(args.image)
        if frame is None:
            print(f"Could not read image: {args.image}")
            return
    else:
        cap = cv2.VideoCapture(0)
        ok, frame = cap.read()
        cap.release()
        if not ok:
            print("Could not capture from laptop camera (port 0)")
            return

    print(f"Sending {frame.shape[1]}×{frame.shape[0]} frame to {args.server} ...")
    t0 = time.perf_counter()
    depth = client.get_depth(frame)
    elapsed = time.perf_counter() - t0
    print(f"Depth map received in {elapsed*1000:.0f} ms  shape={depth.shape}  "
          f"min={depth.min():.2f}m  max={depth.max():.2f}m")

    # Normalise to 0-255 for display
    vis = cv2.normalize(depth, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    vis = cv2.applyColorMap(vis, cv2.COLORMAP_INFERNO)
    combined = np.hstack([frame, vis])
    cv2.imshow("Left: original  |  Right: depth (bright = far)", combined)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
