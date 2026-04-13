import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
import tf2_ros
import lgpio
import time
import math

FL_ENC = 4
FR_ENC = 16
RL_ENC = 20
RR_ENC = 21

DIST_PER_PULSE = 0.00628
WHEEL_BASE_X = 0.0925
WHEEL_BASE_Y = 0.0875

class EncoderOdometry(Node):
 def __init__(self):
  super().__init__("encoder_odometry")
  self.h = lgpio.gpiochip_open(4)
  for pin in [FL_ENC, FR_ENC, RL_ENC, RR_ENC]:
   lgpio.gpio_claim_input(self.h, pin)
  self.last_vals = {p: lgpio.gpio_read(self.h, p) for p in [FL_ENC,FR_ENC,RL_ENC,RR_ENC]}
  self.counts = {FL_ENC: 0, FR_ENC: 0, RL_ENC: 0, RR_ENC: 0}
  self.prev = {FL_ENC: 0, FR_ENC: 0, RL_ENC: 0, RR_ENC: 0}
  self.x = 0.0
  self.y = 0.0
  self.yaw = 0.0
  self.pub = self.create_publisher(Odometry, "/wheel_odom", 10)
  self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)
  self.create_timer(0.01, self.poll)
  self.create_timer(0.05, self.publish_odom)
  self.get_logger().info("Encoder odometry ready — polling mode with TF")

 def poll(self):
  for pin in [FL_ENC, FR_ENC, RL_ENC, RR_ENC]:
   val = lgpio.gpio_read(self.h, pin)
   if val != self.last_vals[pin]:
    self.counts[pin] += 1
    self.last_vals[pin] = val

 def publish_odom(self):
  fl = (self.counts[FL_ENC] - self.prev[FL_ENC]) * DIST_PER_PULSE
  fr = (self.counts[FR_ENC] - self.prev[FR_ENC]) * DIST_PER_PULSE
  rl = (self.counts[RL_ENC] - self.prev[RL_ENC]) * DIST_PER_PULSE
  rr = (self.counts[RR_ENC] - self.prev[RR_ENC]) * DIST_PER_PULSE
  for pin in [FL_ENC, FR_ENC, RL_ENC, RR_ENC]:
   self.prev[pin] = self.counts[pin]

  vx = (fl + fr + rl + rr) / 4.0
  vy = 0.0
  vth = (-fl + fr - rl + rr) / (4.0 * (WHEEL_BASE_X + WHEEL_BASE_Y))

  self.x += vx * math.cos(self.yaw) - vy * math.sin(self.yaw)
  self.y += vx * math.sin(self.yaw) + vy * math.cos(self.yaw)
  self.yaw += vth

  now = self.get_clock().now().to_msg()

  msg = Odometry()
  msg.header.stamp = now
  msg.header.frame_id = "odom"
  msg.child_frame_id = "base_link"
  msg.pose.pose.position.x = self.x
  msg.pose.pose.position.y = self.y
  msg.pose.pose.orientation.x = 0.0
  msg.pose.pose.orientation.y = 0.0
  msg.pose.pose.orientation.z = math.sin(self.yaw / 2.0)
  msg.pose.pose.orientation.w = math.cos(self.yaw / 2.0)
  msg.twist.twist.linear.x = vx / 0.05
  msg.twist.twist.linear.y = vy / 0.05
  msg.twist.twist.angular.z = vth / 0.05

  t = TransformStamped()
  t.header.stamp = now
  t.header.frame_id = 'odom'
  t.child_frame_id = 'base_link'
  t.transform.translation.x = self.x
  t.transform.translation.y = self.y
  t.transform.translation.z = 0.0
  t.transform.rotation.x = 0.0
  t.transform.rotation.y = 0.0
  t.transform.rotation.z = math.sin(self.yaw / 2.0)
  t.transform.rotation.w = math.cos(self.yaw / 2.0)
  self.tf_broadcaster.sendTransform(t)

  self.pub.publish(msg)

 def destroy_node(self):
  lgpio.gpiochip_close(self.h)
  super().destroy_node()

def main(args=None):
 rclpy.init(args=args)
 node = EncoderOdometry()
 try:
  rclpy.spin(node)
 except KeyboardInterrupt:
  pass
 finally:
  node.destroy_node()
  rclpy.shutdown()

if __name__ == "__main__":
 main()
