import math

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data

from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
from std_msgs.msg import Int32

import tf2_ros


DIST_PER_TICK = 0.00628
WHEEL_BASE_X = 0.0925
WHEEL_BASE_Y = 0.0875
KINEMATIC_RADIUS = WHEEL_BASE_X + WHEEL_BASE_Y


def normalize_angle(angle):
    while angle > math.pi:
        angle -= 2.0 * math.pi
    while angle < -math.pi:
        angle += 2.0 * math.pi
    return angle


class Esp32EncoderOdometry(Node):
    def __init__(self):
        super().__init__("esp32_encoder_odometry")

        self.declare_parameter("publish_tf", False)
        self.publish_tf = bool(self.get_parameter("publish_tf").value)

        self.counts = {"FL": None, "FR": None, "RL": None, "RR": None}
        self.prev_counts = None
        self.prev_time = None

        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0

        self.create_subscription(Int32, "/encoders/FL", self._make_count_cb("FL"), qos_profile_sensor_data)
        self.create_subscription(Int32, "/encoders/FR", self._make_count_cb("FR"), qos_profile_sensor_data)
        self.create_subscription(Int32, "/encoders/RL", self._make_count_cb("RL"), qos_profile_sensor_data)
        self.create_subscription(Int32, "/encoders/RR", self._make_count_cb("RR"), qos_profile_sensor_data)

        self.pub = self.create_publisher(Odometry, "/wheel_odom", 10)
        self.tf_broadcaster = tf2_ros.TransformBroadcaster(self) if self.publish_tf else None

        self.create_timer(0.02, self.publish_odom)
        self.get_logger().info(
            "ESP32 encoder odometry ready: /encoders/* -> /wheel_odom at 50Hz"
        )

    def _make_count_cb(self, wheel):
        def callback(msg):
            self.counts[wheel] = int(msg.data)
        return callback

    def have_all_counts(self):
        return all(value is not None for value in self.counts.values())

    def publish_odom(self):
        if not self.have_all_counts():
            return

        now = self.get_clock().now()

        if self.prev_counts is None:
            self.prev_counts = dict(self.counts)
            self.prev_time = now
            return

        dt = (now - self.prev_time).nanoseconds / 1e9
        if dt <= 0.0:
            return

        d_fl = (self.counts["FL"] - self.prev_counts["FL"]) * DIST_PER_TICK
        d_fr = (self.counts["FR"] - self.prev_counts["FR"]) * DIST_PER_TICK
        d_rl = (self.counts["RL"] - self.prev_counts["RL"]) * DIST_PER_TICK
        d_rr = (self.counts["RR"] - self.prev_counts["RR"]) * DIST_PER_TICK

        self.prev_counts = dict(self.counts)
        self.prev_time = now

        body_dx = (d_fl + d_fr + d_rl + d_rr) / 4.0
        body_dy = (-d_fl + d_fr + d_rl - d_rr) / 4.0
        body_dyaw = (-d_fl + d_fr - d_rl + d_rr) / (4.0 * KINEMATIC_RADIUS)

        yaw_mid = self.yaw + body_dyaw * 0.5
        self.x += body_dx * math.cos(yaw_mid) - body_dy * math.sin(yaw_mid)
        self.y += body_dx * math.sin(yaw_mid) + body_dy * math.cos(yaw_mid)
        self.yaw = normalize_angle(self.yaw + body_dyaw)

        vx = body_dx / dt
        vy = body_dy / dt
        wz = body_dyaw / dt

        stamp = now.to_msg()
        qz = math.sin(self.yaw * 0.5)
        qw = math.cos(self.yaw * 0.5)

        msg = Odometry()
        msg.header.stamp = stamp
        msg.header.frame_id = "odom"
        msg.child_frame_id = "base_link"
        msg.pose.pose.position.x = self.x
        msg.pose.pose.position.y = self.y
        msg.pose.pose.position.z = 0.0
        msg.pose.pose.orientation.x = 0.0
        msg.pose.pose.orientation.y = 0.0
        msg.pose.pose.orientation.z = qz
        msg.pose.pose.orientation.w = qw
        msg.twist.twist.linear.x = vx
        msg.twist.twist.linear.y = vy
        msg.twist.twist.angular.z = wz

        msg.pose.covariance[0] = 0.05
        msg.pose.covariance[7] = 0.05
        msg.pose.covariance[35] = 0.20
        msg.twist.covariance[0] = 0.02
        msg.twist.covariance[7] = 0.02
        msg.twist.covariance[35] = 0.05

        self.pub.publish(msg)

        if self.tf_broadcaster is not None:
            transform = TransformStamped()
            transform.header.stamp = stamp
            transform.header.frame_id = "odom"
            transform.child_frame_id = "base_link"
            transform.transform.translation.x = self.x
            transform.transform.translation.y = self.y
            transform.transform.translation.z = 0.0
            transform.transform.rotation.x = 0.0
            transform.transform.rotation.y = 0.0
            transform.transform.rotation.z = qz
            transform.transform.rotation.w = qw
            self.tf_broadcaster.sendTransform(transform)


def main(args=None):
    rclpy.init(args=args)
    node = Esp32EncoderOdometry()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
