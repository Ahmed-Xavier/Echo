import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String
import lgpio
import time

FL_IN1, FL_IN2, FL_PWM = 17, 27, 18
RR_IN1, RR_IN2, RR_PWM = 22, 23, 24
FR_IN1, FR_IN2, FR_PWM = 5, 6, 13
RL_IN1, RL_IN2, RL_PWM = 19, 26, 12
MAX_PWM = 100
TIMEOUT = 0.5

class MotorController(Node):
 def __init__(self):
  super().__init__("motor_controller")
  self.h = lgpio.gpiochip_open(4)
  for p in [FL_IN1,FL_IN2,FL_PWM,RR_IN1,RR_IN2,RR_PWM,
  FR_IN1,FR_IN2,FR_PWM,RL_IN1,RL_IN2,RL_PWM]:
   lgpio.gpio_claim_output(self.h, p)
   lgpio.gpio_write(self.h, p, 0)
  self.stop_all()
  self.get_logger().info("Motor controller ready")
  self.sub_cmd = self.create_subscription(Twist, "/cmd_vel", self.cmd_cb, 10)
  self.sub_mode = self.create_subscription(String, "/robot/mode", self.mode_cb, 10)
  self.timer = self.create_timer(TIMEOUT, self.timeout_cb)
  self.last_cmd = time.time()
  self.mode = "AUTO"

 def set_motor(self, in1, in2, pwm_pin, speed, inverted=False):
  if inverted:
   speed = -speed
  if speed > 0:
   lgpio.gpio_write(self.h, in1, 1)
   lgpio.gpio_write(self.h, in2, 0)
  elif speed < 0:
   lgpio.gpio_write(self.h, in1, 0)
   lgpio.gpio_write(self.h, in2, 1)
  else:
   lgpio.gpio_write(self.h, in1, 0)
   lgpio.gpio_write(self.h, in2, 0)
  duty = min(abs(speed), MAX_PWM)
  lgpio.tx_pwm(self.h, pwm_pin, 100, duty)

 def stop_all(self):
  for in1, in2, pwm in [(FL_IN1,FL_IN2,FL_PWM),(RR_IN1,RR_IN2,RR_PWM),
  (FR_IN1,FR_IN2,FR_PWM),(RL_IN1,RL_IN2,RL_PWM)]:
   lgpio.gpio_write(self.h, in1, 0)
   lgpio.gpio_write(self.h, in2, 0)
   lgpio.tx_pwm(self.h, pwm, 100, 0)

 def cmd_cb(self, msg):
  if self.mode == "EMERGENCY_STOP":
   return
  self.last_cmd = time.time()
  x = msg.linear.x
  y = msg.linear.y
  rot = msg.angular.z
  fl = (x - y - rot) * MAX_PWM
  fr = (x + y + rot) * MAX_PWM
  rl = (x + y - rot) * MAX_PWM
  rr = (x - y + rot) * MAX_PWM
  self.set_motor(FL_IN1, FL_IN2, FL_PWM, fl)
  self.set_motor(FR_IN1, FR_IN2, FR_PWM, fr)
  self.set_motor(RL_IN1, RL_IN2, RL_PWM, rl, inverted=True)
  self.set_motor(RR_IN1, RR_IN2, RR_PWM, rr, inverted=True)

 def mode_cb(self, msg):
  self.mode = msg.data
  if self.mode == "EMERGENCY_STOP":
   self.stop_all()
   self.get_logger().warn("EMERGENCY STOP")

 def timeout_cb(self):
  if time.time() - self.last_cmd > TIMEOUT:
   self.stop_all()

 def destroy_node(self):
  self.stop_all()
  lgpio.gpiochip_close(self.h)
  super().destroy_node()

def main(args=None):
 rclpy.init(args=args)
 node = MotorController()
 try:
  rclpy.spin(node)
 except KeyboardInterrupt:
  pass
 finally:
  node.destroy_node()
  rclpy.shutdown()

if __name__ == "__main__":
 main()
