#!/usr/bin/env python3
import cv2, rclpy, json, sys
from rclpy.node import Node
from std_msgs.msg import String
from pupil_apriltags import Detector

TAG_INSTRUCTIONS = {
    0:"stop", 1:"go_to_goal_A", 2:"go_to_goal_B",
    3:"pause", 4:"resume", 5:"emergency_stop",
    10:"postcard"
}

class AprilTagNode(Node):
    def __init__(self, cam):
        super().__init__("apriltag_detector")
        self.publisher = self.create_publisher(String, "/apriltag/instruction", 10)
        self.detector = Detector(families="tag36h11")
        self.cam = cam
        self.last_tag_id = None
        self.get_logger().info("AprilTag detector started (Headless, Shared Camera)")

    def run(self):
        while rclpy.ok():
            ret, frame = self.cam.read()
            if not ret:
                continue
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            tags = self.detector.detect(gray)
            for tag in tags:
                tag_id = tag.tag_id
                instruction = TAG_INSTRUCTIONS.get(tag_id, f"unknown_tag_{tag_id}")
                if tag_id != self.last_tag_id:
                    self.last_tag_id = tag_id
                    msg = String()
                    msg.data = json.dumps({"tag_id": tag_id, "instruction": instruction, "center": [tag.center[0], tag.center[1]]})
                    self.publisher.publish(msg)
                    self.get_logger().info(f"Tag {tag_id} -> {instruction}")
            if not tags:
                self.last_tag_id = None
            
            # Use small sleep to prevent CPU hogging
            time_to_sleep = 0.05
            rclpy.spin_once(self, timeout_sec=time_to_sleep)

    def destroy_node(self):
        super().destroy_node()

def main():
    # Import shared camera from webrtc_server
    sys.path.insert(0, '/home/ahmed')
    from webrtc_server import shared_cam
    rclpy.init()
    node = AprilTagNode(shared_cam)
    try:
        node.run()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
