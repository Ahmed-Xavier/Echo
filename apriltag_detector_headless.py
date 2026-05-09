#!/usr/bin/env python3
import cv2, rclpy, json, sys
from rclpy.node import Node
from std_msgs.msg import String
from pupil_apriltags import Detector

TAG_INSTRUCTIONS = {
    0:"stop", 1:"go_to_goal_A", 2:"go_to_goal_B",
    3:"pause", 4:"resume", 5:"emergency_stop"
}

class AprilTagNode(Node):
    def __init__(self, cam):
        super().__init__("apriltag_detector")
        self.publisher = self.create_publisher(String, "/apriltag/instruction", 10)
        self.detector = Detector(families="tag36h11")
        self.cam = cam
        self.last_tag_id = None
        self.get_logger().info("AprilTag detector started (shared camera)")

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
            # Draw overlays
            for tag in tags:
                corners = tag.corners.astype(int)
                cv2.polylines(frame, [corners], True, (0,255,0), 2)
                cx, cy = int(tag.center[0]), int(tag.center[1])
                cv2.putText(frame, f"ID:{tag.tag_id}", (cx-20,cy-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
                instr = TAG_INSTRUCTIONS.get(tag.tag_id, f"unknown_{tag.tag_id}")
                cv2.putText(frame, instr, (cx-20,cy+20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,200,255), 2)
            if not tags:
                self.last_tag_id = None
            
            if False:
                break
            rclpy.spin_once(self, timeout_sec=0)

    def destroy_node(self):
        cv2.destroyAllWindows()
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
