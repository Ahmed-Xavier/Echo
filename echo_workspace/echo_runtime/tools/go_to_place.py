#!/usr/bin/env python3
import argparse
import json
import math
import re
from pathlib import Path

import rclpy
from geometry_msgs.msg import PoseStamped
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy


def clean_name(name):
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9_ -]+", "", name)
    name = re.sub(r"[\s-]+", "_", name)
    return name


def quat_from_yaw(yaw):
    return {
        "x": 0.0,
        "y": 0.0,
        "z": math.sin(yaw / 2.0),
        "w": math.cos(yaw / 2.0),
    }


def load_places(path):
    if not path.exists():
        raise SystemExit(f"Places file not found: {path}")

    text = path.read_text().strip()
    if not text:
        return {}

    return json.loads(text)


def main():
    parser = argparse.ArgumentParser(description="Publish a saved place as /goal_pose.")
    parser.add_argument("name", help="Saved place name")
    parser.add_argument("--file", default=str(Path.home() / "echo_runtime/places/places.yaml"))
    parser.add_argument("--topic", default="/goal_pose")
    args = parser.parse_args()

    name = clean_name(args.name)
    path = Path(args.file).expanduser()
    places = load_places(path)

    if name not in places:
        known = ", ".join(sorted(places.keys())) or "none"
        raise SystemExit(f"Unknown place: {name}. Known places: {known}")

    place = places[name]

    rclpy.init()
    node = rclpy.create_node("echo_go_to_place")
    qos = QoSProfile(
        history=HistoryPolicy.KEEP_LAST,
        depth=10,
        reliability=ReliabilityPolicy.RELIABLE,
        durability=DurabilityPolicy.TRANSIENT_LOCAL,
    )
    pub = node.create_publisher(PoseStamped, args.topic, qos)

    msg = PoseStamped()
    msg.header.stamp = node.get_clock().now().to_msg()
    msg.header.frame_id = place.get("frame", "map")
    msg.pose.position.x = float(place["x"])
    msg.pose.position.y = float(place["y"])
    msg.pose.position.z = 0.0

    q = quat_from_yaw(float(place["yaw"]))
    msg.pose.orientation.x = q["x"]
    msg.pose.orientation.y = q["y"]
    msg.pose.orientation.z = q["z"]
    msg.pose.orientation.w = q["w"]

    # Give ROS discovery time to see subscribers such as `ros2 topic echo`,
    # rosbridge, Foxglove, or Nav2.
    deadline = node.get_clock().now().nanoseconds + int(3.0 * 1e9)
    while rclpy.ok() and node.get_clock().now().nanoseconds < deadline:
        if pub.get_subscription_count() > 0:
            break
        rclpy.spin_once(node, timeout_sec=0.1)

    # Publish for a short window so late subscribers can receive the goal.
    for _ in range(30):
        msg.header.stamp = node.get_clock().now().to_msg()
        pub.publish(msg)
        rclpy.spin_once(node, timeout_sec=0.1)

    print(f"[go_to_place] subscribers={pub.get_subscription_count()}")
    print(f"[go_to_place] published {name} to {args.topic}")
    print(f"[go_to_place] frame={msg.header.frame_id} x={msg.pose.position.x:.3f} y={msg.pose.position.y:.3f} yaw={place['yaw']:.3f}")

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
