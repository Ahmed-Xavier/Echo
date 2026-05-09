#!/usr/bin/env python3
import math

import rclpy
from geometry_msgs.msg import TransformStamped, Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import JointState
from tf2_ros import TransformBroadcaster


def yaw_to_quaternion(yaw):
    half_yaw = yaw * 0.5
    return {
        "x": 0.0,
        "y": 0.0,
        "z": math.sin(half_yaw),
        "w": math.cos(half_yaw),
    }


def normalize_angle(angle):
    return math.atan2(math.sin(angle), math.cos(angle))


class RvizCmdVelSim(Node):
    def __init__(self):
        super().__init__("rviz_cmd_vel_sim")

        self.declare_parameter("cmd_vel_topic", "/cmd_vel")
        self.declare_parameter("odom_topic", "/odom")
        self.declare_parameter("odom_frame", "odom")
        self.declare_parameter("base_frame", "base_footprint")
        self.declare_parameter("update_rate", 50.0)
        self.declare_parameter("cmd_timeout", 0.5)
        self.declare_parameter("wheel_radius", 0.040)
        self.declare_parameter("wheel_pos_x", 0.0925)
        self.declare_parameter("wheel_pos_y", 0.0875)

        self.cmd_vel_topic = str(self.get_parameter("cmd_vel_topic").value)
        self.odom_topic = str(self.get_parameter("odom_topic").value)
        self.odom_frame = str(self.get_parameter("odom_frame").value)
        self.base_frame = str(self.get_parameter("base_frame").value)
        self.update_rate = float(self.get_parameter("update_rate").value)
        self.cmd_timeout = float(self.get_parameter("cmd_timeout").value)
        self.wheel_radius = float(self.get_parameter("wheel_radius").value)
        self.wheel_pos_x = float(self.get_parameter("wheel_pos_x").value)
        self.wheel_pos_y = float(self.get_parameter("wheel_pos_y").value)

        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.last_cmd_time = None
        self.last_update_time = self.get_clock().now()
        self.cmd = Twist()

        self.wheel_positions = {
            "front_left_wheel_joint": 0.0,
            "front_right_wheel_joint": 0.0,
            "rear_left_wheel_joint": 0.0,
            "rear_right_wheel_joint": 0.0,
        }

        self.create_subscription(Twist, self.cmd_vel_topic, self.cmd_callback, 10)
        self.odom_pub = self.create_publisher(Odometry, self.odom_topic, 10)
        self.joint_pub = self.create_publisher(JointState, "/joint_states", 10)
        self.tf_broadcaster = TransformBroadcaster(self)

        period = 1.0 / max(self.update_rate, 1.0)
        self.create_timer(period, self.update)

        self.get_logger().info(
            f"RViz cmd_vel sim listening on {self.cmd_vel_topic}, publishing {self.odom_topic} "
            f"and {self.odom_frame}->{self.base_frame}"
        )

    def cmd_callback(self, msg):
        self.cmd = msg
        self.last_cmd_time = self.get_clock().now()

    def active_command(self, now):
        if self.last_cmd_time is None:
            return 0.0, 0.0, 0.0

        age = (now - self.last_cmd_time).nanoseconds / 1e9
        if age > self.cmd_timeout:
            return 0.0, 0.0, 0.0

        return self.cmd.linear.x, self.cmd.linear.y, self.cmd.angular.z

    def update(self):
        now = self.get_clock().now()
        dt = (now - self.last_update_time).nanoseconds / 1e9
        self.last_update_time = now

        if dt <= 0.0:
            return

        dt = min(dt, 0.1)
        vx, vy, wz = self.active_command(now)

        cos_yaw = math.cos(self.yaw)
        sin_yaw = math.sin(self.yaw)
        self.x += (vx * cos_yaw - vy * sin_yaw) * dt
        self.y += (vx * sin_yaw + vy * cos_yaw) * dt
        self.yaw = normalize_angle(self.yaw + wz * dt)

        wheel_velocities = self.wheel_velocities(vx, vy, wz)
        for name, velocity in wheel_velocities.items():
            self.wheel_positions[name] += velocity * dt

        stamp = now.to_msg()
        quat = yaw_to_quaternion(self.yaw)

        self.publish_transform(stamp, quat)
        self.publish_odom(stamp, quat, vx, vy, wz)
        self.publish_joint_states(stamp, wheel_velocities)

    def wheel_velocities(self, vx, vy, wz):
        radius = max(self.wheel_radius, 1e-6)
        angular_term = (self.wheel_pos_x + self.wheel_pos_y) * wz

        return {
            "front_left_wheel_joint": (vx - vy - angular_term) / radius,
            "front_right_wheel_joint": (vx + vy + angular_term) / radius,
            "rear_left_wheel_joint": (vx + vy - angular_term) / radius,
            "rear_right_wheel_joint": (vx - vy + angular_term) / radius,
        }

    def publish_transform(self, stamp, quat):
        transform = TransformStamped()
        transform.header.stamp = stamp
        transform.header.frame_id = self.odom_frame
        transform.child_frame_id = self.base_frame
        transform.transform.translation.x = self.x
        transform.transform.translation.y = self.y
        transform.transform.translation.z = 0.0
        transform.transform.rotation.x = quat["x"]
        transform.transform.rotation.y = quat["y"]
        transform.transform.rotation.z = quat["z"]
        transform.transform.rotation.w = quat["w"]
        self.tf_broadcaster.sendTransform(transform)

    def publish_odom(self, stamp, quat, vx, vy, wz):
        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = self.odom_frame
        odom.child_frame_id = self.base_frame
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.position.z = 0.0
        odom.pose.pose.orientation.x = quat["x"]
        odom.pose.pose.orientation.y = quat["y"]
        odom.pose.pose.orientation.z = quat["z"]
        odom.pose.pose.orientation.w = quat["w"]
        odom.twist.twist.linear.x = vx
        odom.twist.twist.linear.y = vy
        odom.twist.twist.angular.z = wz
        self.odom_pub.publish(odom)

    def publish_joint_states(self, stamp, wheel_velocities):
        joints = JointState()
        joints.header.stamp = stamp
        joints.name = list(self.wheel_positions.keys())
        joints.position = [self.wheel_positions[name] for name in joints.name]
        joints.velocity = [wheel_velocities[name] for name in joints.name]
        self.joint_pub.publish(joints)


def main():
    rclpy.init()
    node = RvizCmdVelSim()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
