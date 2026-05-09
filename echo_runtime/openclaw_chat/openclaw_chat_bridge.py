#!/usr/bin/env python3
import json
import subprocess
import threading

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class OpenClawChatBridge(Node):
    def __init__(self):
        super().__init__("openclaw_chat_bridge")
        self.declare_parameter("agent", "main")
        self.declare_parameter("thinking", "low")
        self.pub = self.create_publisher(String, "/openclaw/chat/response", 10)
        self.sub = self.create_subscription(String, "/openclaw/chat/request", self.on_request, 10)
        self.get_logger().info("OpenClaw chat bridge online: /openclaw/chat/request -> /openclaw/chat/response")

    def on_request(self, msg):
        raw = msg.data or ""
        try:
            payload = json.loads(raw)
            text = payload.get("text") or payload.get("message") or raw
            robot = payload.get("robot", "Echo")
        except Exception:
            text = raw
            robot = "Echo"

        text = text.strip()
        if not text:
            return

        threading.Thread(target=self.ask_openclaw, args=(text, robot), daemon=True).start()

    def ask_openclaw(self, text, robot):
        agent = self.get_parameter("agent").value
        thinking = self.get_parameter("thinking").value

        self.get_logger().info(f"Dashboard chat request for {robot}: {text}")

        try:
            result = subprocess.run(
                ["openclaw", "agent", "--agent", agent, "--message", text, "--thinking", thinking],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=90,
            )
            response = result.stdout.strip() or f"OpenClaw exited with code {result.returncode}."
            if result.returncode != 0:
                response = f"OpenClaw error code {result.returncode}:\n{response}"
        except subprocess.TimeoutExpired:
            response = "OpenClaw took too long to respond."
        except Exception as exc:
            response = f"OpenClaw chat bridge error: {exc}"

        out = {
            "robot": robot,
            "text": response,
        }
        self.pub.publish(String(data=json.dumps(out)))


def main():
    rclpy.init()
    node = OpenClawChatBridge()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
