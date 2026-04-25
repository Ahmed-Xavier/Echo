#!/usr/bin/env python3
import asyncio
import json
import threading
import time

import cv2
import numpy as np
import rclpy
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from av import VideoFrame
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage


class RosCompressedImageStore(Node):
    def __init__(self):
        super().__init__("echo_webrtc_camera_bridge")
        self.lock = threading.Lock()
        self.frame = np.zeros((480, 640, 3), dtype=np.uint8)
        self.last_frame_time = 0.0
        self.create_subscription(
            CompressedImage,
            "/echo/camera/image/compressed",
            self.image_callback,
            10,
        )
        self.get_logger().info("WebRTC bridge subscribed to /echo/camera/image/compressed")

    def image_callback(self, msg):
        encoded = np.frombuffer(msg.data, dtype=np.uint8)
        frame = cv2.imdecode(encoded, cv2.IMREAD_COLOR)

        if frame is None:
            self.get_logger().warn("Failed to decode compressed camera frame", throttle_duration_sec=2.0)
            return

        with self.lock:
            self.frame = frame
            self.last_frame_time = time.monotonic()

    def read(self):
        with self.lock:
            return self.frame.copy(), self.last_frame_time


rclpy.init()
image_store = RosCompressedImageStore()
ros_thread = threading.Thread(target=rclpy.spin, args=(image_store,), daemon=True)
ros_thread.start()

pcs = set()


class CameraTrack(VideoStreamTrack):
    kind = "video"

    async def recv(self):
        pts, time_base = await self.next_timestamp()
        frame, _ = image_store.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        vf = VideoFrame.from_ndarray(frame, format="rgb24")
        vf.pts = pts
        vf.time_base = time_base
        return vf


async def index(request):
    html = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Echo Camera</title>
  <style>
    body { margin: 0; background: #111; color: white; font-family: sans-serif; }
    video { width: 100vw; height: 100vh; object-fit: contain; background: black; }
  </style>
</head>
<body>
  <video id="video" autoplay playsinline muted></video>
  <script>
    async function start() {
      const pc = new RTCPeerConnection();
      pc.addTransceiver("video", { direction: "recvonly" });
      pc.ontrack = (event) => {
        document.getElementById("video").srcObject = event.streams[0];
      };

      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      const response = await fetch("/offer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(pc.localDescription)
      });

      const answer = await response.json();
      await pc.setRemoteDescription(answer);
    }

    start();
  </script>
</body>
</html>
"""
    return web.Response(text=html, content_type="text/html")


async def offer(request):
    params = await request.json()
    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("connectionstatechange")
    async def on_state():
        print(f"WebRTC: {pc.connectionState}")
        if pc.connectionState in ("failed", "closed"):
            await pc.close()
            pcs.discard(pc)

    pc.addTrack(CameraTrack())
    await pc.setRemoteDescription(RTCSessionDescription(sdp=params["sdp"], type=params["type"]))
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.json_response(
        {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type},
        headers={"Access-Control-Allow-Origin": "*"},
    )


async def health(request):
    _, last_frame_time = image_store.read()
    age = time.monotonic() - last_frame_time if last_frame_time else None
    return web.json_response({"ok": age is not None and age < 2.0, "last_frame_age": age})


async def on_shutdown(app):
    await asyncio.gather(*(pc.close() for pc in pcs), return_exceptions=True)
    pcs.clear()
    image_store.destroy_node()
    rclpy.shutdown()


app = web.Application()
app.on_shutdown.append(on_shutdown)
app.router.add_get("/", index)
app.router.add_get("/health", health)
app.router.add_post("/offer", offer)

if __name__ == "__main__":
    print("Echo WebRTC camera bridge on http://0.0.0.0:8081")
    web.run_app(app, host="0.0.0.0", port=8081)

