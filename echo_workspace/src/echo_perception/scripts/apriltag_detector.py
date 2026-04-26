#!/usr/bin/env python3
import json
import math
import time

import cv2
import numpy as np
import rclpy
from pupil_apriltags import Detector
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage, Image
from std_msgs.msg import String
from visualization_msgs.msg import Marker, MarkerArray


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

        self.declare_parameter("input_topic", "/echo/camera/image_raw")
        self.declare_parameter("instruction_topic", "/apriltag/instruction")
        self.declare_parameter("annotated_topic", "/apriltag/annotated_image/compressed")
        self.declare_parameter("marker_topic", "/apriltag/markers")
        self.declare_parameter("publish_rate", 5.0)
        self.declare_parameter("jpeg_quality", 70)

        # Approximate camera intrinsics for 640x480 until we calibrate.
        self.declare_parameter("fx", 600.0)
        self.declare_parameter("fy", 600.0)
        self.declare_parameter("cx", 320.0)
        self.declare_parameter("cy", 240.0)
        self.declare_parameter("tag_size", 0.08)
        self.declare_parameter("camera_frame", "camera_link")

        self.input_topic = self.get_parameter("input_topic").value
        self.instruction_topic = self.get_parameter("instruction_topic").value
        self.annotated_topic = self.get_parameter("annotated_topic").value
        self.marker_topic = self.get_parameter("marker_topic").value
        self.publish_period = 1.0 / max(float(self.get_parameter("publish_rate").value), 0.1)
        self.jpeg_quality = int(self.get_parameter("jpeg_quality").value)

        self.fx = float(self.get_parameter("fx").value)
        self.fy = float(self.get_parameter("fy").value)
        self.cx = float(self.get_parameter("cx").value)
        self.cy = float(self.get_parameter("cy").value)
        self.tag_size = float(self.get_parameter("tag_size").value)
        self.camera_frame = self.get_parameter("camera_frame").value

        self.instruction_pub = self.create_publisher(String, self.instruction_topic, 10)
        self.annotated_pub = self.create_publisher(CompressedImage, self.annotated_topic, 10)
        self.marker_pub = self.create_publisher(MarkerArray, self.marker_topic, 10)

        self.create_subscription(Image, self.input_topic, self.image_callback, 10)

        self.detector = Detector(families="tag36h11")
        self.last_publish_time = 0.0

        self.get_logger().info(f"AprilTag detector subscribed to {self.input_topic}")
        self.get_logger().info(f"Publishing instructions on {self.instruction_topic}")
        self.get_logger().info(f"Publishing annotated image on {self.annotated_topic}")
        self.get_logger().info(f"Publishing 3D markers on {self.marker_topic}")

    def image_callback(self, msg):
        frame = np.frombuffer(msg.data, dtype=np.uint8).reshape((msg.height, msg.width, 3))

        if msg.encoding == "rgb8":
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        elif msg.encoding != "bgr8":
            self.get_logger().warn(
                f"Unsupported image encoding: {msg.encoding}",
                throttle_duration_sec=2.0,
            )
            return

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        tags = self.detector.detect(gray)

        annotated = frame.copy()
        for tag in tags:
            self.draw_tag(annotated, tag)

        self.publish_annotated_image(annotated, msg.header)
        self.publish_markers(tags, msg.header)

        if not tags:
            return

        now = time.monotonic()
        if now - self.last_publish_time < self.publish_period:
            return

        self.last_publish_time = now
        self.publish_instruction(tags[0])

    def publish_instruction(self, tag):
        tag_id = int(tag.tag_id)
        instruction = TAG_INSTRUCTIONS.get(tag_id, f"unknown_tag_{tag_id}")

        out = String()
        out.data = json.dumps(
            {
                "tag_id": tag_id,
                "instruction": instruction,
                "center": [float(tag.center[0]), float(tag.center[1])],
            }
        )
        self.instruction_pub.publish(out)
        self.get_logger().info(f"Tag {tag_id} -> {instruction}", throttle_duration_sec=1.0)

    def draw_tag(self, frame, tag):
        corners = np.array(tag.corners, dtype=np.int32)
        center = tuple(np.array(tag.center, dtype=np.int32))

        tag_id = int(tag.tag_id)
        instruction = TAG_INSTRUCTIONS.get(tag_id, f"unknown_tag_{tag_id}")

        cv2.polylines(frame, [corners], isClosed=True, color=(0, 255, 120), thickness=3)
        cv2.circle(frame, center, 5, (0, 120, 255), -1)

        label = f"ID {tag_id}: {instruction}"
        x = max(int(corners[:, 0].min()), 0)
        y = max(int(corners[:, 1].min()) - 10, 20)

        cv2.putText(frame, label, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(frame, label, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)

    def publish_annotated_image(self, frame, header):
        ok, encoded = cv2.imencode(
            ".jpg",
            frame,
            [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality],
        )
        if not ok:
            self.get_logger().warn("Failed to encode annotated image", throttle_duration_sec=2.0)
            return

        msg = CompressedImage()
        msg.header = header
        msg.format = "jpeg"
        msg.data = encoded.tobytes()
        self.annotated_pub.publish(msg)

    def publish_markers(self, tags, header):
        markers = MarkerArray()
        stamp = header.stamp

        # Clear old markers every frame, so disappeared tags disappear in Foxglove.
        clear = Marker()
        clear.header.stamp = stamp
        clear.header.frame_id = self.camera_frame
        clear.action = Marker.DELETEALL
        markers.markers.append(clear)

        for index, tag in enumerate(tags):
            tag_id = int(tag.tag_id)
            instruction = TAG_INSTRUCTIONS.get(tag_id, f"unknown_tag_{tag_id}")
            x, y, z = self.estimate_camera_point(tag)

            sphere = Marker()
            sphere.header.stamp = stamp
            sphere.header.frame_id = self.camera_frame
            sphere.ns = "apriltag"
            sphere.id = tag_id * 2
            sphere.type = Marker.SPHERE
            sphere.action = Marker.ADD
            sphere.pose.position.x = x
            sphere.pose.position.y = y
            sphere.pose.position.z = z
            sphere.pose.orientation.w = 1.0
            sphere.scale.x = 0.07
            sphere.scale.y = 0.07
            sphere.scale.z = 0.07
            sphere.color.r = 1.0
            sphere.color.g = 0.65
            sphere.color.b = 0.05
            sphere.color.a = 1.0
            markers.markers.append(sphere)

            text = Marker()
            text.header.stamp = stamp
            text.header.frame_id = self.camera_frame
            text.ns = "apriltag_label"
            text.id = tag_id * 2 + 1
            text.type = Marker.TEXT_VIEW_FACING
            text.action = Marker.ADD
            text.pose.position.x = x
            text.pose.position.y = y
            text.pose.position.z = z + 0.12
            text.pose.orientation.w = 1.0
            text.scale.z = 0.08
            text.color.r = 1.0
            text.color.g = 1.0
            text.color.b = 1.0
            text.color.a = 1.0
            text.text = f"Tag {tag_id}: {instruction}"
            markers.markers.append(text)

        self.marker_pub.publish(markers)

    def estimate_camera_point(self, tag):
        # Approximate depth using pinhole projection:
        # apparent_pixel_size = focal_length * real_size / depth
        corners = np.array(tag.corners, dtype=np.float32)
        side_lengths = [
            np.linalg.norm(corners[0] - corners[1]),
            np.linalg.norm(corners[1] - corners[2]),
            np.linalg.norm(corners[2] - corners[3]),
            np.linalg.norm(corners[3] - corners[0]),
        ]
        pixel_size = max(float(np.mean(side_lengths)), 1.0)
        depth = (self.fx * self.tag_size) / pixel_size

        u = float(tag.center[0])
        v = float(tag.center[1])

        # ROS optical frame would be z-forward, x-right, y-down.
        # Our URDF camera_link is not optical, but this gives a useful Foxglove marker.
        x_forward = depth
        y_left = -((u - self.cx) / self.fx) * depth
        z_up = -((v - self.cy) / self.fy) * depth

        return x_forward, y_left, z_up


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
