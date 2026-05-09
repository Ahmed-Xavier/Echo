#!/usr/bin/env python3
import asyncio, json, cv2, threading, numpy as np
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from av import VideoFrame

# ── Shared camera ──────────────────────────────────────────
class SharedCamera:
    def __init__(self, index=8):
        self.cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 20)
        self.frame = np.zeros((480, 640, 3), dtype=np.uint8)
        self.lock = threading.Lock()
        self.running = True
        threading.Thread(target=self._capture, daemon=True).start()

    def _capture(self):
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.frame = frame

    def read(self):
        with self.lock:
            return True, self.frame.copy()

    def release(self):
        self.running = False
        self.cap.release()

shared_cam = SharedCamera(0)
pcs = set()

# ── WebRTC track ───────────────────────────────────────────
class CameraTrack(VideoStreamTrack):
    kind = "video"
    async def recv(self):
        pts, time_base = await self.next_timestamp()
        ret, frame = shared_cam.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        vf = VideoFrame.from_ndarray(frame, format="rgb24")
        vf.pts = pts
        vf.time_base = time_base
        return vf

# ── HTTP handlers ──────────────────────────────────────────
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

    return web.Response(
        content_type="application/json",
        text=json.dumps({"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}),
        headers={"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "Content-Type"}
    )

async def options(request):
    return web.Response(headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST",
        "Access-Control-Allow-Headers": "Content-Type"
    })

async def on_shutdown(app):
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()
    shared_cam.release()

app = web.Application()
app.on_shutdown.append(on_shutdown)
app.router.add_post("/offer", offer)
app.router.add_options("/offer", options)

if __name__ == "__main__":
    print("WebRTC server on http://0.0.0.0:8081")
    web.run_app(app, host="0.0.0.0", port=8081)
