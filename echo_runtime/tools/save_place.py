#!/usr/bin/env python3
import argparse
import json
import math
import re
import sys
from pathlib import Path

import rclpy
from rclpy.duration import Duration
from tf2_ros import Buffer, TransformListener


def yaw_from_quat(q):
    siny = 2.0 * (q.w * q.z + q.x * q.y)
    cosy = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny, cosy)


def clean_name(name):
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9_ -]+", "", name)
    name = re.sub(r"[\s-]+", "_", name)
    return name


def load_places(path):
    if not path.exists():
        return {}

    text = path.read_text().strip()
    if not text:
        return {}

    # JSON is valid YAML 1.2 and easy to parse without extra dependencies.
    try:
        return json.loads(text)
    except Exception:
        print(f"[save_place] Could not parse {path}. Back it up before editing.", file=sys.stderr)
        raise


def save_places(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Save current Echo pose as a named place.")
    parser.add_argument("name", help="Place name, e.g. kitchen, dock, hallway_start")
    parser.add_argument("--file", default=str(Path.home() / "echo_runtime/places/places.yaml"))
    parser.add_argument("--target-frame", default="map")
    parser.add_argument("--source-frame", default="base_link")
    parser.add_argument("--timeout", type=float, default=8.0)
    args = parser.parse_args()

    name = clean_name(args.name)
    if not name:
        raise SystemExit("Place name became empty after cleaning.")

    rclpy.init()
    node = rclpy.create_node("echo_save_place")
    buffer = Buffer()
    listener = TransformListener(buffer, node)

    deadline = node.get_clock().now() + Duration(seconds=args.timeout)
    transform = None

    while rclpy.ok() and node.get_clock().now() < deadline:
        rclpy.spin_once(node, timeout_sec=0.1)
        try:
            transform = buffer.lookup_transform(
                args.target_frame,
                args.source_frame,
                rclpy.time.Time(),
                timeout=Duration(seconds=0.2),
            )
            break
        except Exception:
            pass

    if transform is None:
        node.destroy_node()
        rclpy.shutdown()
        raise SystemExit(
            f"Could not read TF {args.target_frame} -> {args.source_frame}. "
            "Make sure mapping/localization is running."
        )

    t = transform.transform.translation
    q = transform.transform.rotation
    yaw = yaw_from_quat(q)

    path = Path(args.file).expanduser()
    places = load_places(path)

    places[name] = {
        "frame": args.target_frame,
        "x": round(float(t.x), 4),
        "y": round(float(t.y), 4),
        "yaw": round(float(yaw), 4),
        "yaw_deg": round(math.degrees(yaw), 2),
        "source_frame": args.source_frame,
    }

    save_places(path, places)

    print(f"[save_place] saved {name}")
    print(f"[save_place] file: {path}")
    print(f"[save_place] pose: x={t.x:.3f} y={t.y:.3f} yaw={yaw:.3f} rad / {math.degrees(yaw):.1f} deg")

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
