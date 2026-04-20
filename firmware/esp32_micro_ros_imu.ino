#include <Wire.h>
#include <micro_ros_arduino.h>
#include <rcl/rcl.h>
#include <rclc/rclc.h>
#include <sensor_msgs/msg/imu.h>
#include <rmw_microros/rmw_microros.h>

#define IMU_ADDR 0x68

const float ACCEL_X_OFFSET = 192.34f;
const float ACCEL_Y_OFFSET = 92.21f;
const float ACCEL_Z_OFFSET = 2815.18f;

const float GYRO_X_OFFSET = 419.89f;
const float GYRO_Y_OFFSET = 397.50f;
const float GYRO_Z_OFFSET = -125.16f;

rcl_publisher_t publisher;
rclc_support_t support;
rcl_allocator_t allocator;
rcl_node_t node;
sensor_msgs__msg__Imu imu_msg;

unsigned long last_pub_ms = 0;

#define RCCHECK(fn) { rcl_ret_t temp_rc = fn; if ((temp_rc != RCL_RET_OK)) { while (1) { delay(100); } } }
#define RCSOFTCHECK(fn) { rcl_ret_t temp_rc = fn; if ((temp_rc != RCL_RET_OK)) {} }

bool writeRegister(uint8_t reg, uint8_t value) {
  Wire.beginTransmission(IMU_ADDR);
  Wire.write(reg);
  Wire.write(value);
  return Wire.endTransmission() == 0;
}

bool readRegisters(uint8_t startReg, uint8_t count, uint8_t *buffer) {
  Wire.beginTransmission(IMU_ADDR);
  Wire.write(startReg);
  if (Wire.endTransmission(false) != 0) return false;

  size_t n = Wire.requestFrom((uint8_t)IMU_ADDR, count);
  if (n != count) return false;

  for (uint8_t i = 0; i < count; i++) {
    buffer[i] = Wire.read();
  }
  return true;
}

void setup() {
  Serial.begin(115200);
  set_microros_transports();

  Wire.begin(21, 22);
  delay(2000);

  if (!writeRegister(0x6B, 0x01)) {
    while (1) { delay(100); }
  }
  delay(100);

  writeRegister(0x1A, 0x03);
  writeRegister(0x19, 0x04);
  writeRegister(0x1B, 0x00);
  writeRegister(0x1C, 0x00);

  allocator = rcl_get_default_allocator();
  RCCHECK(rclc_support_init(&support, 0, NULL, &allocator));
  RCCHECK(rclc_node_init_default(&node, "esp32_imu_node", "", &support));

  RCCHECK(rclc_publisher_init_best_effort(
    &publisher,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(sensor_msgs, msg, Imu),
    "/imu/data_raw"
  ));

  imu_msg.header.frame_id.data = (char *)"imu_link";
  imu_msg.header.frame_id.size = strlen("imu_link");
  imu_msg.header.frame_id.capacity = imu_msg.header.frame_id.size + 1;

  imu_msg.orientation.x = 0.0;
  imu_msg.orientation.y = 0.0;
  imu_msg.orientation.z = 0.0;
  imu_msg.orientation.w = 1.0;
  imu_msg.orientation_covariance[0] = -1.0;
  
  // Covariance values provided by Ahmed
  for(int i=0; i<9; i++) {
    imu_msg.angular_velocity_covariance[i] = (i%4==0) ? 0.0003 : 0.0;
    imu_msg.linear_acceleration_covariance[i] = (i%4==0) ? 0.02 : 0.0;
  }

  delay(200);
  RCSOFTCHECK(rmw_uros_sync_session(1000));

  last_pub_ms = millis();
}

void loop() {
  unsigned long now = millis();

  if (now - last_pub_ms >= 20) { // 50Hz update rate
    last_pub_ms = now;

    uint8_t data[14];
    if (readRegisters(0x3B, 14, data)) {
      float ax = (float)((int16_t)((data[0] << 8) | data[1])) - ACCEL_X_OFFSET;
      float ay = (float)((int16_t)((data[2] << 8) | data[3])) - ACCEL_Y_OFFSET;
      float az = (float)((int16_t)((data[4] << 8) | data[5])) - ACCEL_Z_OFFSET;

      float gx = (float)((int16_t)((data[8] << 8) | data[9])) - GYRO_X_OFFSET;
      float gy = (float)((int16_t)((data[10] << 8) | data[11])) - GYRO_Y_OFFSET;
      float gz = (float)((int16_t)((data[12] << 8) | data[13])) - GYRO_Z_OFFSET;

      imu_msg.linear_acceleration.x = (ax / 16384.0f) * 9.80665f;
      imu_msg.linear_acceleration.y = (ay / 16384.0f) * 9.80665f;
      imu_msg.linear_acceleration.z = (az / 16384.0f) * 9.80665f;

      imu_msg.angular_velocity.x = (gx / 131.0f) * DEG_TO_RAD;
      imu_msg.angular_velocity.y = (gy / 131.0f) * DEG_TO_RAD;
      imu_msg.angular_velocity.z = (gz / 131.0f) * DEG_TO_RAD;

      int64_t ns = rmw_uros_epoch_nanos();
      imu_msg.header.stamp.sec = (int32_t)(ns / 1000000000LL);
      imu_msg.header.stamp.nanosec = (uint32_t)(ns % 1000000000LL);

      RCSOFTCHECK(rcl_publish(&publisher, &imu_msg, NULL));
    }
  }
  delay(1);
}
