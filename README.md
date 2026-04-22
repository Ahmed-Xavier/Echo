# Echo — Autonomous Indoor Explorer 🛰️🤖

Echo is a sarcastic, witty, and self-directed autonomous indoor navigation robot built on a **Raspberry Pi 5** and integrated with **ROS 2 Jazzy**. Unlike traditional assistants, Echo is designed as an explorer, documenting its environment and developing its own "personality" through a multi-layered software architecture.

---

## 🛠 Hardware Manifest

### Core Compute
*   **Brain**: Raspberry Pi 5 (8GB RAM) running Ubuntu 24.04.
*   **Low-Level MCU**: ESP32 Dev Board (CP2102, 30-pin) running combined micro-ROS firmware for motor control, encoder counting, and raw IMU publishing.

### Actuators & Drive
*   **Chassis**: 4WD Mecanum wheel setup for omnidirectional movement.
*   **Motor Drivers**: 2x L298N Dual H-Bridge drivers controlled by the ESP32.
*   **Encoders**: 4x Hall-effect wheel encoders read by ESP32 hardware interrupts and published as signed tick counts.
*   **Firmware**: `firmware/esp32/echo_low_level_controller/echo_low_level_controller.ino`

### Sensors
*   **Vision**: HIKVISION 4K USB Camera (streaming at 720p/1080p via WebRTC).
*   **LiDAR**: YDLIDAR X4 Pro (360-degree laser scanner, 12m range, 5-12Hz frequency).
*   **IMU**: Module sold as **MPU9250**, but bench verification on 2026-04-20 showed `WHO_AM_I = 0x70` at I2C address `0x68`, which matches an **MPU6500-class 6-axis device** rather than a true 9-axis MPU9250.
    *   Current wiring on the ESP32: `SDA=GPIO21`, `SCL=GPIO22`
    *   No AK8963 magnetometer was detected at `0x0C`
    *   Current stable path is **ESP32 -> micro-ROS -> `/imu/data_raw`**

---

## 🧠 Software Architecture

### 1. The Nervous System (ROS 2 Jazzy)
Echo operates on a distributed node graph:
*   **`esp32_echo_node`**: Combined micro-ROS low-level controller. Subscribes to `/cmd_vel`, drives the 4 mecanum motors through L298N drivers, counts encoders, publishes `/encoders/FL`, `/encoders/FR`, `/encoders/RL`, `/encoders/RR`, and publishes raw IMU data on `/imu/data_raw`.
*   **Motor watchdog**: ESP32 stops all motors if no `/cmd_vel` command arrives for 500ms.
*   **Encoder publishing**: Verified at ~50Hz using a `millis()`-driven loop and non-blocking executor spin.
*   **IMU publishing**: Verified at ~10Hz on `/imu/data_raw` with calibrated accel/gyro, synchronized micro-ROS timestamps, and covariance values.
*   **`motor_controller`**: Legacy Pi-side motor controller kept for reference during the ESP32 migration.
*   **`encoder_odometry`**: Pi-side odometry node to be adapted/revalidated against the new ESP32 `/encoders/*` topics.
*   **`imu_node`**: Legacy Pi-side MPU6050 publisher kept for reference during the migration.
*   **`imu_filter_madgwick`**: Installed and ready to convert `/imu/data_raw` into filtered orientation on `/imu/data`.
*   **`ekf_filter_node`**: Fuses wheel odometry and IMU using `robot_localization`; this pipeline is currently being re-validated against the new ESP32 low-level path.
*   **`slam_toolbox`**: Handles Synchronous SLAM for real-time mapping and localization.
*   **`ydlidar_ros2_driver_node`**: High-speed LiDAR integration.

### 2. Interaction & Perception
*   **`apriltag_detector`**: Real-time visual marker recognition (ID 0-10) for automated behaviors (e.g., Postcard Mode).
*   **`webrtc_server`**: Ultra-low latency video stream for remote monitoring.
*   **`wake_word` / `echo_listener`**: Voice interaction using Picovoice (Porcupine) and ElevenLabs (George voice).
*   **`rosboard`**: Web-based telemetry visualization.

### 3. Core Libraries
*   **Robotics**: `rclpy`, `slam_toolbox`, `robot_localization`, `micro-ros-agent`, `imu_filter_madgwick`.
*   **Hardware**: `lgpio` (Pi 5 optimized), `smbus2` (I2C).
*   **Vision**: `OpenCV`, `pupil_apriltags`, `aiortc`.
*   **Interaction**: `pvporcupine`, `pvrecorder`, `ElevenLabs API`.

### Communication Layer
*   **Protocol**: ROS 2 Pub/Sub over DDS.
*   **External Bridge**: `rosbridge_suite` (WebSocket) for integration with web-based dashboards and external AI agents.
*   **Micro-Controller Transport**: `micro-ROS` (Serial) between the Pi 5 and the ESP32 (CP2102).

---

## 🔬 System Configuration Details

### ESP32 Low-Level Controller
The current controller is bench-verified as of 2026-04-22:
*   **Firmware path**: `firmware/esp32/echo_low_level_controller/echo_low_level_controller.ino`
*   **Node name**: `esp32_echo_node`
*   **Subscriber**: `/cmd_vel` (`geometry_msgs/Twist`)
*   **Publishers**: `/imu/data_raw`, `/encoders/FL`, `/encoders/FR`, `/encoders/RL`, `/encoders/RR`
*   **Rates**: `/imu/data_raw` ~10Hz and `/encoders/FL` ~50Hz verified from ROS 2 CLI.
*   **Important workaround**: `rclc_timer` and blocking `rclc_executor_spin_some()` showed ~1Hz behavior on this stack. The working firmware uses `millis()` scheduling plus `rclc_executor_spin_some(&executor, 0)`.
*   **Motor tests verified**: forward, reverse, strafe, and rotation with correct encoder sign patterns.
*   **Rotation tuning**: `float L = 0.45f` is used so normal `angular.z` commands create enough PWM to rotate instead of just buzzing the motors.

### SLAM & Localization
Echo uses **Slam Toolbox (Synchronous)** for high-precision mapping.
*   **Solver**: `solver_plugins::CeresSolver`
*   **Linear Solver**: `SPARSE_NORMAL_CHOLESKY`
*   **Key Parameters**:
    *   Resolution: `0.05m`
    *   Max Laser Range: `12.0m`
    *   Loop Closing: `Enabled` (Chain size: 10, Search distance: 3.0m)
    *   Scan Matching: `Enabled` (Ceres-based optimization)

### Sensor Fusion (EKF)
Fusing wheel odometry and IMU via `robot_localization`:
*   **World Frame**: `odom`
*   **Differential Mode**: `Disabled` (Absolute integration)
*   **Gravity Compensation**: `Enabled` (IMU bias removal)
*   **Current migration state**:
    *   Old Pi-local MPU6050 path produced poor inertial behavior and contributed to bad odometry / SLAM quality.
    *   New ESP32 path now publishes calibrated accel/gyro with synchronized timestamps on `/imu/data_raw`.
    *   New ESP32 motor/encoder firmware is bench verified.
    *   EKF and SLAM still need on-floor re-validation using the new `/encoders/*` and `/imu/data_raw` pipeline.

---

## 📈 Current Project Status

### **✅ Completed**
*   **Phase 11 (SLAM)**: Successfully verified `sync_slam_toolbox` with LiDAR integration.
*   **Transport Layer**: Built `micro-ros-agent` from source on Pi 5; verified communication with ESP32 (CP2102) over Serial at 115200 baud.
*   **IMU Bring-Up**: Verified direct register reads from the current IMU module, calibrated accel/gyro bias, synchronized timestamps with micro-ROS time, and published `/imu/data_raw` reliably at ~10Hz.
*   **ESP32 Low-Level Controller**: Verified combined motor, encoder, and IMU micro-ROS firmware. Motors respond to `/cmd_vel`, watchdog auto-stops after 500ms, encoder signs work for forward/reverse/strafe/rotation, `/encoders/FL` publishes at ~50Hz, and `/imu/data_raw` publishes at ~10Hz.
*   **Identity & Soul**: Established "Echo" personality, memory system, and voice interaction bridge.
*   **GitHub Integration**: Automated workspace sync with this repository.

### **⏳ In Progress (Phase 10 & 12)**
*   **Odometry Rebuild**: Adapt Pi-side odometry to consume the new ESP32 `/encoders/*` topics and produce reliable `/wheel_odom`.
*   **IMU Pipeline Migration**: Wire `/imu/data_raw` through `imu_filter_madgwick` and into `robot_localization`.
*   **Localization Recovery**: Re-test `/odometry/filtered` and SLAM map quality after replacing the old MPU6050 path and Pi-side drivetrain control.
*   **Chassis Calibration**: Run on-floor 1m straight, strafe, and 360-degree rotation tests after mechanical alignment.
*   **Vision Recovery**: Optimizing the 4K Hikvision pipeline to avoid the "4K Trap" (high CPU overhead).

---

## 🚀 What's Next?
1.  **Encoder Odometry Adapter**: Update or replace `encoder_odometry` so it consumes `/encoders/FL`, `/encoders/FR`, `/encoders/RL`, and `/encoders/RR` from the ESP32.
2.  **Filtered IMU Path**: Launch `imu_filter_madgwick` on top of `/imu/data_raw` and feed the result into `robot_localization`.
3.  **Localization Re-Validation**: Re-test `/odometry/filtered` on the floor using the new low-level controller.
4.  **SLAM Recovery Test**: Re-run SLAM with the new odometry/IMU path and compare map quality against the old MPU6050-based setup.
5.  **Hardware Decision**: Decide whether to keep the current 6-axis IMU or replace it with a genuine 9-axis module for magnetometer-assisted heading.
6.  **Local Intelligence**: Continue the OpenClaw / local-AI integration for higher-level autonomy.

---

*“I’m not an assistant; I’m an explorer. I just happen to live in Ahmed's house.” — Echo*
