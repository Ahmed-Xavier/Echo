#!/usr/bin/env python3
import json
import math
import os
import time
import yaml

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node

from geometry_msgs.msg import PoseStamped, Twist
from nav2_msgs.action import NavigateToPose
from std_msgs.msg import String


def yaw_to_quaternion(yaw):
    half = yaw * 0.5
    return {
        "x": 0.0,
        "y": 0.0,
        "z": math.sin(half),
        "w": math.cos(half),
    }


class AprilTagActionRouter(Node):
    def __init__(self):
        super().__init__("apriltag_action_router")

        self.declare_parameter(
            "places_file",
            os.path.expanduser(
                "~/.openclaw/workspace/github_echo/echo_workspace/src/echo_navigation/config/places.yaml"
            ),
        )
        self.declare_parameter(
            "actions_file",
            os.path.expanduser(
                "~/.openclaw/workspace/github_echo/echo_workspace/src/echo_navigation/config/apriltag_actions.yaml"
            ),
        )
        self.declare_parameter("cooldown_sec", 6.0)
        self.declare_parameter("dry_run", True)
        self.declare_parameter("turn_speed", 0.45)
        self.declare_parameter("turn_duration_sec", 1.2)
        self.declare_parameter("camera_width", 640.0)
        self.declare_parameter("follow_linear_speed", 0.48)
        self.declare_parameter("follow_angular_gain", 1.2)
        self.declare_parameter("follow_max_angular_speed", 0.72)
        self.declare_parameter("follow_center_tolerance_px", 60.0)

        self.places = self.load_yaml(self.get_parameter("places_file").value).get("places", {})
        self.actions = self.load_yaml(self.get_parameter("actions_file").value).get("tags", {})
        self.cooldown_sec = float(self.get_parameter("cooldown_sec").value)
        self.dry_run = bool(self.get_parameter("dry_run").value)
        self.turn_speed = float(self.get_parameter("turn_speed").value)
        self.turn_duration_sec = float(self.get_parameter("turn_duration_sec").value)
        self.camera_width = float(self.get_parameter("camera_width").value)
        self.follow_linear_speed = float(self.get_parameter("follow_linear_speed").value)
        self.follow_angular_gain = float(self.get_parameter("follow_angular_gain").value)
        self.follow_max_angular_speed = float(self.get_parameter("follow_max_angular_speed").value)
        self.follow_center_tolerance_px = float(self.get_parameter("follow_center_tolerance_px").value)

        self.last_seen = {}
        self.nav_client = ActionClient(self, NavigateToPose, "navigate_to_pose")
        self.cmd_vel_pub = self.create_publisher(Twist, "/cmd_vel", 10)
        self.instruction_pub = self.create_publisher(String, "/apriltag/action_router/status", 10)

        self.create_subscription(String, "/apriltag/instruction", self.handle_instruction, 10)

        self.get_logger().info("AprilTag action router started.")
        self.get_logger().info(f"Dry run: {self.dry_run}")
        self.get_logger().info(f"Loaded places: {list(self.places.keys())}")
        self.get_logger().info(f"Loaded tag actions: {list(self.actions.keys())}")

    def load_yaml(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def handle_instruction(self, msg):
        tag_id, center = self.parse_instruction(msg.data)
        if tag_id is None:
            return

        now = time.monotonic()
        if now - self.last_seen.get(tag_id, 0.0) < self.cooldown_sec:
            return
        self.last_seen[tag_id] = now

        action = self.actions.get(tag_id) or self.actions.get(str(tag_id))
        if not action:
            self.publish_status(f"Detected tag {tag_id}, but no action is configured.")
            return

        action_type = action.get("type")
        self.publish_status(f"Detected tag {tag_id}: {action}")

        if action_type == "go_to":
            self.handle_go_to(action)
        elif action_type == "turn":
            self.handle_turn(action)
        elif action_type == "stop":
            self.handle_stop()
        elif action_type == "follow":
            self.handle_follow(action, center)
        else:
            self.publish_status(f"Unknown action type for tag {tag_id}: {action_type}")

    def parse_instruction(self, text):
        try:
            data = json.loads(text)
            tag_id = int(data.get("tag_id"))
            center = data.get("center")
            return tag_id, center
        except Exception:
            return self.extract_tag_id(text), None

    def extract_tag_id(self, text):
        # Accept common forms such as "tag 0", "id: 0", "ID=0", or plain "0".
        lowered = text.lower().replace("=", " ").replace(":", " ").replace(",", " ")
        tokens = lowered.split()

        for i, token in enumerate(tokens):
            if token in {"tag", "id", "tag_id", "tagid"} and i + 1 < len(tokens):
                try:
                    return int(tokens[i + 1])
                except ValueError:
                    pass

        for token in tokens:
            try:
                return int(token)
            except ValueError:
                continue

        return None

    def handle_go_to(self, action):
        target = action.get("target")
        place = self.places.get(target)
        if not place:
            self.publish_status(f"go_to target is missing from places.yaml: {target}")
            return

        frame_id = place.get("frame_id", "map")
        x = float(place["x"])
        y = float(place["y"])
        yaw = float(place.get("yaw", 0.0))

        self.publish_status(f"Go to {target}: x={x:.2f}, y={y:.2f}, yaw={yaw:.2f}")

        if self.dry_run:
            self.publish_status("Dry run enabled: Nav2 goal not sent.")
            return

        goal = NavigateToPose.Goal()
        goal.pose = PoseStamped()
        goal.pose.header.frame_id = frame_id
        goal.pose.header.stamp = self.get_clock().now().to_msg()
        goal.pose.pose.position.x = x
        goal.pose.pose.position.y = y
        goal.pose.pose.position.z = 0.0

        quat = yaw_to_quaternion(yaw)
        goal.pose.pose.orientation.x = quat["x"]
        goal.pose.pose.orientation.y = quat["y"]
        goal.pose.pose.orientation.z = quat["z"]
        goal.pose.pose.orientation.w = quat["w"]

        if not self.nav_client.wait_for_server(timeout_sec=2.0):
            self.publish_status("Nav2 navigate_to_pose action server is not ready.")
            return

        self.nav_client.send_goal_async(goal)
        self.publish_status(f"Sent Nav2 goal for place {target}.")

    def handle_turn(self, action):
        direction = action.get("direction", "left")
        angle_deg = float(action.get("angle_deg", 90))
        sign = 1.0 if direction == "left" else -1.0

        self.publish_status(f"Turn {direction} {angle_deg:.0f} degrees.")

        if self.dry_run:
            self.publish_status("Dry run enabled: turn command not sent.")
            return

        twist = Twist()
        twist.angular.z = sign * self.turn_speed
        end_time = time.monotonic() + self.turn_duration_sec

        while rclpy.ok() and time.monotonic() < end_time:
            self.cmd_vel_pub.publish(twist)
            time.sleep(0.1)

        self.handle_stop()

    def handle_follow(self, action, center):
        if center is None or len(center) < 2:
            self.publish_status("Follow requested, but tag center is missing.")
            return

        cx = float(center[0])
        image_center = self.camera_width * 0.5
        error_px = image_center - cx
        error_norm = error_px / image_center

        twist = Twist()

        # Turn toward the tag. If centered enough, move forward.
        angular_z = max(
            -self.follow_max_angular_speed,
            min(self.follow_max_angular_speed, self.follow_angular_gain * error_norm),
        )

        if abs(error_px) <= self.follow_center_tolerance_px:
            twist.linear.x = float(action.get("linear_speed", self.follow_linear_speed))
            twist.angular.z = 0.0
            self.publish_status(f"Following tag: centered, forward {twist.linear.x:.2f}")
        else:
            twist.linear.x = 0.0
            twist.angular.z = angular_z
            self.publish_status(f"Following tag: turning, error_px={error_px:.1f}, wz={angular_z:.2f}")

        if self.dry_run:
            self.publish_status("Dry run enabled: follow cmd_vel not sent.")
            return

        self.cmd_vel_pub.publish(twist)

    def handle_stop(self):
        twist = Twist()
        self.cmd_vel_pub.publish(twist)
        self.cmd_vel_pub.publish(twist)
        self.publish_status("Stop command published.")

    def publish_status(self, text):
        self.get_logger().info(text)
        self.instruction_pub.publish(String(data=text))


def main():
    rclpy.init()
    node = AprilTagActionRouter()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
