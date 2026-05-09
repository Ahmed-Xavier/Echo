#!/usr/bin/env python3
import cv2
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage, Image


class EchoCameraPublisher(Node):
    def __init__(self):
        super().__init__("echo_camera_publisher")

        self.declare_parameter("camera_index", 0)
        self.declare_parameter("width", 640)
        self.declare_parameter("height", 480)
        self.declare_parameter("fps", 15.0)
        self.declare_parameter("frame_id", "camera_link")
        self.declare_parameter("jpeg_quality", 75)

        self.camera_index = int(self.get_parameter("camera_index").value)
        self.width = int(self.get_parameter("width").value)
        self.height = int(self.get_parameter("height").value)
        self.fps = float(self.get_parameter("fps").value)
        self.frame_id = str(self.get_parameter("frame_id").value)
        self.jpeg_quality = int(self.get_parameter("jpeg_quality").value)

        self.raw_pub = self.create_publisher(Image, "/echo/camera/image_raw", 10)
        self.jpeg_pub = self.create_publisher(CompressedImage, "/echo/camera/image/compressed", 10)

        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)

        if not self.cap.isOpened():
            self.get_logger().error(f"Failed to open camera index {self.camera_index}")
        else:
            self.get_logger().info(f"Publishing camera {self.camera_index} on /echo/camera/image_raw")

        self.timer = self.create_timer(1.0 / max(self.fps, 1.0), self.publish_frame)

    def publish_frame(self):
        ok, frame = self.cap.read()
        if not ok:
            self.get_logger().warn("Camera frame read failed", throttle_duration_sec=2.0)
            return

        stamp = self.get_clock().now().to_msg()

        raw = Image()
        raw.header.stamp = stamp
        raw.header.frame_id = self.frame_id
        raw.height = frame.shape[0]
        raw.width = frame.shape[1]
        raw.encoding = "bgr8"
        raw.is_bigendian = False
        raw.step = frame.shape[1] * frame.shape[2]
        raw.data = frame.tobytes()
        self.raw_pub.publish(raw)

        ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality])
        if ok:
            jpeg = CompressedImage()
            jpeg.header.stamp = stamp
            jpeg.header.frame_id = self.frame_id
            jpeg.format = "jpeg"
            jpeg.data = encoded.tobytes()
            self.jpeg_pub.publish(jpeg)

    def destroy_node(self):
        self.cap.release()
        super().destroy_node()


def main():
    rclpy.init()
    node = EchoCameraPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
