#!/usr/bin/env python3
import json

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from pupil_apriltags import Detector


TAG_INSTRUCTIONS = {
    0: "stop",
    1: "go_to_goal_A",
    2: "go_to_goal_B",
    3: "pause",
    4: "resume",
    5: "emergency_stop",
    10: "postcard",
}


class AprilTagNode(Node):
    def __init__(self):
        super().__init__("apriltag_detector")
        self.publisher = self.create_publisher(String, "/apriltag/instruction", 10)
        self.subscription = self.create_subscription(
            Image,
            "/echo/camera/image_raw",
            self.image_callback,
            10,
        )
        self.detector = Detector(families="tag36h11")
        self.last_tag_id = None
        self.get_logger().info("AprilTag detector subscribed to /echo/camera/image_raw")

    def image_callback(self, msg):
        frame = np.frombuffer(msg.data, dtype=np.uint8).reshape(
            (msg.height, msg.width, 3)
        )

        if msg.encoding == "rgb8":
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        tags = self.detector.detect(gray)

        if not tags:
            self.last_tag_id = None
            return

        for tag in tags:
            tag_id = tag.tag_id
            instruction = TAG_INSTRUCTIONS.get(tag_id, f"unknown_tag_{tag_id}")

            if tag_id == self.last_tag_id:
                continue

            self.last_tag_id = tag_id
            out = String()
            out.data = json.dumps(
                {
                    "tag_id": tag_id,
                    "instruction": instruction,
                    "center": [float(tag.center[0]), float(tag.center[1])],
                }
            )
            self.publisher.publish(out)
            self.get_logger().info(f"Tag {tag_id} -> {instruction}")


def main():
    rclpy.init()
    node = AprilTagNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

