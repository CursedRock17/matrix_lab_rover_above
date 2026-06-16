"""
Depth Anything 3 GPU inference server — run this on the desktop with the NVIDIA GPU.

Accepts JPEG image bytes over HTTP POST /depth and returns a raw float32 depth map
(metric meters, same coordinate convention as the ArUco estimator: +Z forward).

One GPU worker thread serializes all inference so the GPU is never double-booked.
Incoming requests queue up (FIFO) and are served in order; the sender blocks until
its result is ready.  A /health endpoint lets clients confirm the server is up.

Usage:
    python depth_server.py                     # default port 5000
    python depth_server.py --port 5000 --host 0.0.0.0
"""

import argparse
import queue
import threading
import time

import cv2
import numpy as np
import torch
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from PIL import Image
from transformers import pipeline

# ---------------------------------------------------------------------------
# Model configuration
# ---------------------------------------------------------------------------
# Verify this ID on https://huggingface.co/depth-anything before your first run.
# The naming convention follows Depth Anything V2 (e.g. "depth-anything/Depth-Anything-V2-Large-hf").
# For V3 Large the expected ID is shown below — check the model card for the exact string.
MODEL_ID = "depth-anything/Depth-Anything-V3-Large-hf"

# Maximum number of requests allowed to wait in the queue before the server starts
# rejecting new ones with HTTP 503.  Keeps memory usage bounded if the GPU falls behind.
MAX_QUEUE_DEPTH = 20  # sized for a full class of ~15 rovers bunching up simultaneously

# ---------------------------------------------------------------------------
# Shared state (populated during startup, read by the endpoint)
# ---------------------------------------------------------------------------
_work_queue: queue.Queue = queue.Queue(maxsize=MAX_QUEUE_DEPTH)
_depth_pipe = None   # set during lifespan startup
_worker_thread = None
_ready = threading.Event()


def _gpu_worker(pipe):
    """
    Pulls (jpeg_bytes, result_dict, done_event) tuples from the queue one at a time
    and runs Depth Anything 3 on the GPU.  Results are written back into result_dict
    before done_event is set so the waiting HTTP handler can return them.
    """
    _ready.set()
    while True:
        item = _work_queue.get()
        if item is None:        # sentinel: shut down cleanly
            break
        jpeg_bytes, result, done = item
        try:
            buf = np.frombuffer(jpeg_bytes, np.uint8)
            frame = cv2.imdecode(buf, cv2.IMREAD_COLOR)
            if frame is None:
                raise ValueError("Could not decode JPEG — is the payload a valid image?")

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            output = pipe(Image.fromarray(rgb))

            # predicted_depth: raw metric tensor (H×W), values in meters
            depth = output["predicted_depth"].squeeze().cpu().numpy().astype(np.float32)
            result["depth"] = depth
            result["shape"] = depth.shape   # (H, W)
        except Exception as exc:
            result["error"] = str(exc)
        finally:
            done.set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _depth_pipe, _worker_thread

    if not torch.cuda.is_available():
        raise RuntimeError(
            "No CUDA GPU detected.  This server must run on the desktop with the NVIDIA GPU.\n"
            "Check that the CUDA-enabled PyTorch is installed (see README)."
        )

    device_name = torch.cuda.get_device_name(0)
    print(f"Loading {MODEL_ID} onto {device_name} ...")
    t0 = time.perf_counter()

    # torch_dtype=torch.float16 keeps weights as 16-bit floats (half precision).
    # This is NOT quantization — it is the standard GPU inference format and has
    # no meaningful accuracy impact for depth estimation.  Do not use int8/int4.
    _depth_pipe = pipeline(
        "depth-estimation",
        model=MODEL_ID,
        device=0,
        torch_dtype=torch.float16,
    )

    print(f"Model loaded in {time.perf_counter() - t0:.1f}s")

    _worker_thread = threading.Thread(target=_gpu_worker, args=(_depth_pipe,), daemon=True)
    _worker_thread.start()
    _ready.wait()       # block until the worker confirms it is running
    print(f"Depth server ready — listening for JPEG frames")

    yield   # server runs here

    # Shutdown: drain the queue and stop the worker
    _work_queue.put(None)
    if _worker_thread is not None:
        _worker_thread.join(timeout=5.0)


app = FastAPI(lifespan=lifespan)


@app.get("/health")
def health():
    """Quick liveness check.  Returns 200 + GPU name when the server is up."""
    return {
        "status": "ok",
        "model": MODEL_ID,
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "none",
        "queue_depth": _work_queue.qsize(),
    }


@app.post("/depth")
async def depth_endpoint(request: Request):
    """
    POST a raw JPEG body to this endpoint.
    Returns raw float32 bytes (row-major, metric meters) with two headers:
        X-Depth-Height   image height in pixels
        X-Depth-Width    image width in pixels

    Reconstruct on the client with:
        h = int(resp.headers["X-Depth-Height"])
        w = int(resp.headers["X-Depth-Width"])
        depth = np.frombuffer(resp.content, dtype=np.float32).reshape(h, w)
    """
    jpeg_bytes = await request.body()
    if not jpeg_bytes:
        raise HTTPException(status_code=400, detail="Empty request body — send a JPEG image.")

    result: dict = {}
    done = threading.Event()

    try:
        _work_queue.put_nowait((jpeg_bytes, result, done))
    except queue.Full:
        raise HTTPException(
            status_code=503,
            detail=f"Server queue is full ({MAX_QUEUE_DEPTH} requests waiting). Try again shortly.",
        )

    # Wait for the GPU worker to finish without blocking the async event loop
    import asyncio
    await asyncio.get_event_loop().run_in_executor(None, done.wait, 30.0)

    if not done.is_set():
        raise HTTPException(status_code=504, detail="Depth inference timed out after 30 s.")

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    depth: np.ndarray = result["depth"]
    h, w = result["shape"]

    return Response(
        content=depth.tobytes(),
        media_type="application/octet-stream",
        headers={"X-Depth-Height": str(h), "X-Depth-Width": str(w)},
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Depth Anything 3 GPU inference server")
    parser.add_argument("--host", default="0.0.0.0", help="Interface to bind (default: all)")
    parser.add_argument("--port", type=int, default=5000, help="Port to listen on (default: 5000)")
    args = parser.parse_args()

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
