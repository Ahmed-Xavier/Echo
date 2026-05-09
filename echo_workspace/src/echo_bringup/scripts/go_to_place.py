#!/usr/bin/env python3
import math
import sys
from pathlib import Path

import rclpy
import yaml
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from rclpy.node import Node


DEFAULT_PLACES_FILE = (
    Path.home()
    / ".openclaw/workspace/github_echo/echo_workspace/src/echo_navigation/config/places.yaml"
)


def yaw_to_quat(yaw):
    half = yaw * 0.5
    return 0.0, 0.0, math.sin(half), math.cos(half)


class GoToPlace(Node):
    def __init__(self, place_name):
        super().__init__("go_to_place")
        self.place_name = place_name
        self.declare_parameter("places_file", str(DEFAULT_PLACES_FILE))
        self.client = ActionClient(self, NavigateToPose, "navigate_to_pose")

    def run(self):
        places_file = Path(self.get_parameter("places_file").value).expanduser()
        places = yaml.safe_load(places_file.read_text()) or {}
        places = places.get("places", {})

        if self.place_name not in places:
            known = ", ".join(sorted(places)) or "none"
            raise SystemExit(f"Unknown place '{self.place_name}'. Known places: {known}")

        place = places[self.place_name]
        frame_id = place.get("frame_id", "map")
        x = float(place["x"])
        y = float(place["y"])
        yaw = float(place.get("yaw", 0.0))
        qx, qy, qz, qw = yaw_to_quat(yaw)

        goal = NavigateToPose.Goal()
        goal.pose = PoseStamped()
        goal.pose.header.frame_id = frame_id
        goal.pose.header.stamp = self.get_clock().now().to_msg()
        goal.pose.pose.position.x = x
        goal.pose.pose.position.y = y
        goal.pose.pose.position.z = 0.0
        goal.pose.pose.orientation.x = qx
        goal.pose.pose.orientation.y = qy
        goal.pose.pose.orientation.z = qz
        goal.pose.pose.orientation.w = qw

        self.get_logger().info(
            f"Going to {self.place_name}: frame={frame_id}, x={x:.3f}, y={y:.3f}, yaw={yaw:.3f}"
        )

        if not self.client.wait_for_server(timeout_sec=5.0):
            raise SystemExit("Nav2 navigate_to_pose action server is not ready.")

        send_future = self.client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, send_future)
        goal_handle = send_future.result()

        if not goal_handle or not goal_handle.accepted:
            raise SystemExit("Goal rejected by Nav2.")

        self.get_logger().info("Goal accepted by Nav2.")


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: go_to_place.py PLACE_NAME")

    rclpy.init()
    node = GoToPlace(sys.argv[1])
    try:
        node.run()
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
