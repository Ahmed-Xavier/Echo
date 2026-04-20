#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
import smbus2
import math
import time

MPU6050_ADDR = 0x68
PWR_MGMT_1   = 0x6B
ACCEL_XOUT_H = 0x3B
GYRO_XOUT_H  = 0x43

ACCEL_SCALE  = 16384.0  # ±2g
GYRO_SCALE   = 131.0    # ±250 deg/s

class ImuNode(Node):
    def __init__(self):
        super().__init__('imu_node')
        self.bus = smbus2.SMBus(1)
        self.bus.write_byte_data(MPU6050_ADDR, PWR_MGMT_1, 0)
        time.sleep(0.1)

        # Calibration offsets (gyro bias)
        self.gx_offset = 0.0
        self.gy_offset = 0.0
        self.gz_offset = 0.0
        self.calibrate()

        self.publisher = self.create_publisher(Imu, '/imu/data', 10)
        self.create_timer(0.02, self.publish_imu)  # 50Hz
        self.get_logger().info('IMU node started at 50Hz')

    def read_word(self, reg):
        high = self.bus.read_byte_data(MPU6050_ADDR, reg)
        low  = self.bus.read_byte_data(MPU6050_ADDR, reg + 1)
        val  = (high << 8) + low
        return val - 65536 if val >= 32768 else val

    def calibrate(self):
        self.get_logger().info('Calibrating IMU — keep still for 2 seconds...')
        samples = 200
        gx_sum = gy_sum = gz_sum = 0.0
        for _ in range(samples):
            gx_sum += self.read_word(GYRO_XOUT_H)
            gy_sum += self.read_word(GYRO_XOUT_H + 2)
            gz_sum += self.read_word(GYRO_XOUT_H + 4)
            time.sleep(0.01)
        self.gx_offset = gx_sum / samples / GYRO_SCALE
        self.gy_offset = gy_sum / samples / GYRO_SCALE
        self.gz_offset = gz_sum / samples / GYRO_SCALE
        self.get_logger().info(f'Calibration done. Offsets: gx={self.gx_offset:.3f} gy={self.gy_offset:.3f} gz={self.gz_offset:.3f}')

    def publish_imu(self):
        ax = self.read_word(ACCEL_XOUT_H)     / ACCEL_SCALE * 9.81
        ay = self.read_word(ACCEL_XOUT_H + 2) / ACCEL_SCALE * 9.81
        az = self.read_word(ACCEL_XOUT_H + 4) / ACCEL_SCALE * 9.81
        gx = self.read_word(GYRO_XOUT_H)      / GYRO_SCALE  - self.gx_offset
        gy = self.read_word(GYRO_XOUT_H + 2)  / GYRO_SCALE  - self.gy_offset
        gz = self.read_word(GYRO_XOUT_H + 4)  / GYRO_SCALE  - self.gz_offset

        msg = Imu()
        msg.header.stamp    = self.get_clock().now().to_msg()
        msg.header.frame_id = 'imu_link'

        msg.linear_acceleration.x = ax
        msg.linear_acceleration.y = ay
        msg.linear_acceleration.z = az

        msg.angular_velocity.x = math.radians(gx)
        msg.angular_velocity.y = math.radians(gy)
        msg.angular_velocity.z = math.radians(gz)

        # No orientation from raw MPU6050 (EKF will compute it)
        msg.orientation_covariance[0] = -1.0

        self.publisher.publish(msg)

def main():
    rclpy.init()
    node = ImuNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
