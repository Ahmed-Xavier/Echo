#include <Arduino.h>
#include <Wire.h>
#include <math.h>

#include <micro_ros_arduino.h>
#include <rcl/rcl.h>
#include <rclc/rclc.h>
#include <rclc/executor.h>
#include <geometry_msgs/msg/twist.h>
#include <sensor_msgs/msg/imu.h>
#include <std_msgs/msg/int32.h>
#include <rmw_microros/rmw_microros.h>

// Serial agent baud
#define MICRO_ROS_BAUD 115200

// Publish rates
#define ENCODER_PUBLISH_PERIOD_MS 20   // 50 Hz
#define IMU_PUBLISH_PERIOD_MS     100  // 10 Hz, safer at 115200 baud

// Encoder pins
#define ENCODER_FL 4
#define ENCODER_FR 16
#define ENCODER_RL 17
#define ENCODER_RR 18

// Motor pins
#define FL_ENA 14
#define FL_IN1 13
#define FL_IN2 12

#define RR_ENB 27
#define RR_IN3 25
#define RR_IN4 26

#define FR_ENA 23
#define FR_IN1 5
#define FR_IN2 19

#define RL_ENB 15
#define RL_IN3 33
#define RL_IN4 32

// IMU pins are fixed in Wire.begin(21, 22)
#define IMU_ADDR 0x68

const float ACCEL_X_OFFSET = 192.34f;
const float ACCEL_Y_OFFSET = 92.21f;
const float ACCEL_Z_OFFSET = 2815.18f;

const float GYRO_X_OFFSET = 419.89f;
const float GYRO_Y_OFFSET = 397.50f;
const float GYRO_Z_OFFSET = -125.16f;

// PWM
#define PWM_FREQ 1000
#define PWM_RES 8

// Safety
#define CMD_TIMEOUT_MS 500

// micro-ROS
rcl_subscription_t sub_cmdvel;

rcl_publisher_t pub_imu;
rcl_publisher_t pub_enc_FL;
rcl_publisher_t pub_enc_FR;
rcl_publisher_t pub_enc_RL;
rcl_publisher_t pub_enc_RR;

geometry_msgs__msg__Twist twist_msg;
sensor_msgs__msg__Imu imu_msg;

std_msgs__msg__Int32 enc_FL_msg;
std_msgs__msg__Int32 enc_FR_msg;
std_msgs__msg__Int32 enc_RL_msg;
std_msgs__msg__Int32 enc_RR_msg;

rclc_executor_t executor;
rclc_support_t support;
rcl_allocator_t allocator;
rcl_node_t node;

#define RCCHECK(fn) { rcl_ret_t temp_rc = fn; if ((temp_rc != RCL_RET_OK)) { stopAll(); while (1) { delay(100); } } }
#define RCSOFTCHECK(fn) { rcl_ret_t temp_rc = fn; if ((temp_rc != RCL_RET_OK)) {} }

// Encoder state
portMUX_TYPE encoder_mux = portMUX_INITIALIZER_UNLOCKED;

volatile int32_t count_FL = 0;
volatile int32_t count_FR = 0;
volatile int32_t count_RL = 0;
volatile int32_t count_RR = 0;

// Direction is estimated from commanded motor direction.
// This is good for one-channel encoders, but true quadrature would be better later.
volatile int8_t dir_FL = 0;
volatile int8_t dir_FR = 0;
volatile int8_t dir_RL = 0;
volatile int8_t dir_RR = 0;

void IRAM_ATTR isr_FL() {
  portENTER_CRITICAL_ISR(&encoder_mux);
  count_FL += dir_FL;
  portEXIT_CRITICAL_ISR(&encoder_mux);
}

void IRAM_ATTR isr_FR() {
  portENTER_CRITICAL_ISR(&encoder_mux);
  count_FR += dir_FR;
  portEXIT_CRITICAL_ISR(&encoder_mux);
}

void IRAM_ATTR isr_RL() {
  portENTER_CRITICAL_ISR(&encoder_mux);
  count_RL += dir_RL;
  portEXIT_CRITICAL_ISR(&encoder_mux);
}

void IRAM_ATTR isr_RR() {
  portENTER_CRITICAL_ISR(&encoder_mux);
  count_RR += dir_RR;
  portEXIT_CRITICAL_ISR(&encoder_mux);
}

unsigned long last_cmd_ms = 0;
unsigned long last_encoder_pub_ms = 0;
unsigned long last_imu_pub_ms = 0;

bool motors_active = false;
bool imu_ok = false;

void setEncoderDirection(volatile int8_t *dir, int8_t value) {
  portENTER_CRITICAL(&encoder_mux);
  *dir = value;
  portEXIT_CRITICAL(&encoder_mux);
}

void setWheelMotor(int in1, int in2, int ena, volatile int8_t *enc_dir, float speed) {
  int pwm = (int)(fabsf(speed) * 255.0f);
  pwm = constrain(pwm, 0, 255);

  int8_t direction = 0;

  if (speed > 0.01f) {
    digitalWrite(in1, HIGH);
    digitalWrite(in2, LOW);
    direction = 1;
  } else if (speed < -0.01f) {
    digitalWrite(in1, LOW);
    digitalWrite(in2, HIGH);
    direction = -1;
  } else {
    digitalWrite(in1, LOW);
    digitalWrite(in2, LOW);
    pwm = 0;
    direction = 0;
  }

  setEncoderDirection(enc_dir, direction);
  ledcWrite(ena, pwm);
}

void stopAll() {
  setWheelMotor(FL_IN1, FL_IN2, FL_ENA, &dir_FL, 0.0f);
  setWheelMotor(FR_IN1, FR_IN2, FR_ENA, &dir_FR, 0.0f);
  setWheelMotor(RL_IN3, RL_IN4, RL_ENB, &dir_RL, 0.0f);
  setWheelMotor(RR_IN3, RR_IN4, RR_ENB, &dir_RR, 0.0f);
  motors_active = false;
}

bool writeRegister(uint8_t reg, uint8_t value) {
  Wire.beginTransmission(IMU_ADDR);
  Wire.write(reg);
  Wire.write(value);
  return Wire.endTransmission() == 0;
}

bool readRegisters(uint8_t startReg, uint8_t count, uint8_t *buffer) {
  Wire.beginTransmission(IMU_ADDR);
  Wire.write(startReg);

  if (Wire.endTransmission(false) != 0) {
    return false;
  }

  size_t n = Wire.requestFrom((uint8_t)IMU_ADDR, count);
  if (n != count) {
    return false;
  }

  for (uint8_t i = 0; i < count; i++) {
    buffer[i] = Wire.read();
  }

  return true;
}

void cmd_vel_callback(const void *msgin) {
  const geometry_msgs__msg__Twist *msg = (const geometry_msgs__msg__Twist *)msgin;
  last_cmd_ms = millis();

  float vx = msg->linear.x;
  float vy = msg->linear.y;
  float wz = msg->angular.z;

  // Tune this later after chassis measurement.
  float L = 0.45f;

  float fl = vx - vy - wz * L;
  float fr = vx + vy + wz * L;
  float rl = vx + vy - wz * L;
  float rr = vx - vy + wz * L;

  float max_val = fmaxf(fmaxf(fabsf(fl), fabsf(fr)), fmaxf(fabsf(rl), fabsf(rr)));
  if (max_val < 1.0f) {
    max_val = 1.0f;
  }

  fl /= max_val;
  fr /= max_val;
  rl /= max_val;
  rr /= max_val;

  bool command_active =
    fabsf(fl) > 0.01f ||
    fabsf(fr) > 0.01f ||
    fabsf(rl) > 0.01f ||
    fabsf(rr) > 0.01f;

  if (!command_active) {
    stopAll();
    return;
  }

  setWheelMotor(FL_IN1, FL_IN2, FL_ENA, &dir_FL, fl);
  setWheelMotor(FR_IN1, FR_IN2, FR_ENA, &dir_FR, fr);
  setWheelMotor(RL_IN3, RL_IN4, RL_ENB, &dir_RL, rl);
  setWheelMotor(RR_IN3, RR_IN4, RR_ENB, &dir_RR, rr);

  motors_active = true;
}

void publishEncoders() {
  int32_t fl;
  int32_t fr;
  int32_t rl;
  int32_t rr;

  portENTER_CRITICAL(&encoder_mux);
  fl = count_FL;
  fr = count_FR;
  rl = count_RL;
  rr = count_RR;
  portEXIT_CRITICAL(&encoder_mux);

  enc_FL_msg.data = fl;
  enc_FR_msg.data = fr;
  enc_RL_msg.data = rl;
  enc_RR_msg.data = rr;

  RCSOFTCHECK(rcl_publish(&pub_enc_FL, &enc_FL_msg, NULL));
  RCSOFTCHECK(rcl_publish(&pub_enc_FR, &enc_FR_msg, NULL));
  RCSOFTCHECK(rcl_publish(&pub_enc_RL, &enc_RL_msg, NULL));
  RCSOFTCHECK(rcl_publish(&pub_enc_RR, &enc_RR_msg, NULL));
}

void publishImu() {
  if (!imu_ok) {
    return;
  }

  uint8_t data[14];
  if (!readRegisters(0x3B, 14, data)) {
    return;
  }

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

  RCSOFTCHECK(rcl_publish(&pub_imu, &imu_msg, NULL));
}

void setup() {
  Serial.begin(MICRO_ROS_BAUD);
  set_microros_transports();
  delay(2000);

  pinMode(ENCODER_FL, INPUT_PULLUP);
  pinMode(ENCODER_FR, INPUT_PULLUP);
  pinMode(ENCODER_RL, INPUT_PULLUP);
  pinMode(ENCODER_RR, INPUT_PULLUP);

  attachInterrupt(digitalPinToInterrupt(ENCODER_FL), isr_FL, RISING);
  attachInterrupt(digitalPinToInterrupt(ENCODER_FR), isr_FR, RISING);
  attachInterrupt(digitalPinToInterrupt(ENCODER_RL), isr_RL, RISING);
  attachInterrupt(digitalPinToInterrupt(ENCODER_RR), isr_RR, RISING);

  pinMode(FL_IN1, OUTPUT);
  pinMode(FL_IN2, OUTPUT);
  pinMode(RR_IN3, OUTPUT);
  pinMode(RR_IN4, OUTPUT);
  pinMode(FR_IN1, OUTPUT);
  pinMode(FR_IN2, OUTPUT);
  pinMode(RL_IN3, OUTPUT);
  pinMode(RL_IN4, OUTPUT);

  ledcAttach(FL_ENA, PWM_FREQ, PWM_RES);
  ledcAttach(RR_ENB, PWM_FREQ, PWM_RES);
  ledcAttach(FR_ENA, PWM_FREQ, PWM_RES);
  ledcAttach(RL_ENB, PWM_FREQ, PWM_RES);

  stopAll();

  Wire.begin(21, 22);
  Wire.setClock(400000);
  delay(100);

  imu_ok = true;
  imu_ok &= writeRegister(0x6B, 0x01);
  delay(100);
  imu_ok &= writeRegister(0x1A, 0x03);
  imu_ok &= writeRegister(0x19, 0x04);
  imu_ok &= writeRegister(0x1B, 0x00);
  imu_ok &= writeRegister(0x1C, 0x00);

  allocator = rcl_get_default_allocator();

  RCCHECK(rclc_support_init(&support, 0, NULL, &allocator));
  RCCHECK(rclc_node_init_default(&node, "esp32_echo_node", "", &support));

  RCCHECK(rclc_publisher_init_best_effort(
    &pub_imu,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(sensor_msgs, msg, Imu),
    "/imu/data_raw"
  ));

  RCCHECK(rclc_publisher_init_best_effort(
    &pub_enc_FL,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32),
    "/encoders/FL"
  ));

  RCCHECK(rclc_publisher_init_best_effort(
    &pub_enc_FR,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32),
    "/encoders/FR"
  ));

  RCCHECK(rclc_publisher_init_best_effort(
    &pub_enc_RL,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32),
    "/encoders/RL"
  ));

  RCCHECK(rclc_publisher_init_best_effort(
    &pub_enc_RR,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32),
    "/encoders/RR"
  ));

  RCCHECK(rclc_subscription_init_default(
    &sub_cmdvel,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(geometry_msgs, msg, Twist),
    "/cmd_vel"
  ));

  RCCHECK(rclc_executor_init(&executor, &support.context, 1, &allocator));
  RCCHECK(rclc_executor_add_subscription(
    &executor,
    &sub_cmdvel,
    &twist_msg,
    &cmd_vel_callback,
    ON_NEW_DATA
  ));

  imu_msg.header.frame_id.data = (char *)"imu_link";
  imu_msg.header.frame_id.size = strlen("imu_link");
  imu_msg.header.frame_id.capacity = imu_msg.header.frame_id.size + 1;

  imu_msg.orientation.x = 0.0;
  imu_msg.orientation.y = 0.0;
  imu_msg.orientation.z = 0.0;
  imu_msg.orientation.w = 1.0;

  imu_msg.orientation_covariance[0] = -1.0;

  imu_msg.angular_velocity_covariance[0] = 0.0003;
  imu_msg.angular_velocity_covariance[4] = 0.0003;
  imu_msg.angular_velocity_covariance[8] = 0.0003;

  imu_msg.linear_acceleration_covariance[0] = 0.02;
  imu_msg.linear_acceleration_covariance[4] = 0.02;
  imu_msg.linear_acceleration_covariance[8] = 0.02;

  delay(200);
  RCSOFTCHECK(rmw_uros_sync_session(1000));

  last_cmd_ms = millis();
  last_encoder_pub_ms = millis();
  last_imu_pub_ms = millis();
}

void loop() {
  unsigned long now = millis();

  if (motors_active && (now - last_cmd_ms > CMD_TIMEOUT_MS)) {
    stopAll();
  }

 RCSOFTCHECK(rclc_executor_spin_some(&executor, 0));

  now = millis();

  if (now - last_encoder_pub_ms >= ENCODER_PUBLISH_PERIOD_MS) {
    last_encoder_pub_ms += ENCODER_PUBLISH_PERIOD_MS;
    publishEncoders();
  }

  if (now - last_imu_pub_ms >= IMU_PUBLISH_PERIOD_MS) {
    last_imu_pub_ms += IMU_PUBLISH_PERIOD_MS;
    publishImu();
  }

  delay(1);
}
