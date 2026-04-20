# Echo — Autonomous Indoor Explorer 🛰️🤖

Echo is a sarcastic, witty, and self-directed autonomous indoor navigation robot built on a **Raspberry Pi 5** and integrated with **ROS 2 Jazzy**. Unlike traditional assistants, Echo is designed as an explorer, documenting its environment and developing its own "personality" through a multi-layered software architecture.

---

## 🛠 Hardware Manifest

### Core Compute
*   **Brain**: Raspberry Pi 5 (8GB RAM) running Ubuntu 24.04.
*   **MCU**: ESP32 Dev Board (CP2102, 30-pin) — currently handling the micro-ROS transport layer for low-level sensor and future motor/encoder offloading.

### Actuators & Drive
*   **Chassis**: 4WD Mecanum wheel setup for omnidirectional movement.
*   **Motor Drivers**: 2x L298N Dual H-Bridge drivers.
*   **Encoders**: 4x Hall-effect wheel encoders (polled at 0.00628 meters per pulse).

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
*   **`motor_controller`**: Translates `/cmd_vel` into PWM/Direction signals.
*   **`encoder_odometry`**: Computes wheel-based positioning.
*   **`imu_node`**: Legacy Pi-side MPU6050 publisher kept for reference during the migration.
*   **ESP32 micro-ROS IMU publisher**: Publishes calibrated raw inertial data on **`/imu/data_raw`** at a stable ~10Hz using a `millis()`-driven loop.
*   **`imu_filter_madgwick`**: Installed and ready to convert `/imu/data_raw` into filtered orientation on `/imu/data`.
*   **`ekf_filter_node`**: Fuses wheel odometry and IMU using `robot_localization`; this pipeline is currently being re-validated against the new ESP32 IMU path.
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
    *   EKF and SLAM are being re-validated on the new IMU path before calling localization stable again.

---

## 📈 Current Project Status

### **✅ Completed**
*   **Phase 11 (SLAM)**: Successfully verified `sync_slam_toolbox` with LiDAR integration.
*   **Transport Layer**: Built `micro-ros-agent` from source on Pi 5; verified communication with ESP32 (CP2102) over Serial at 115200 baud.
*   **IMU Bring-Up**: Verified direct register reads from the current IMU module, calibrated accel/gyro bias, synchronized timestamps with micro-ROS time, and published `/imu/data_raw` reliably at ~10Hz.
*   **Identity & Soul**: Established "Echo" personality, memory system, and voice interaction bridge.
*   **GitHub Integration**: Automated workspace sync with this repository.

### **⏳ In Progress (Phase 9b & 12)**
*   **Hardware Offloading**: Migrating motor PWM control and hardware-interrupt encoder reading (PCNT) to the ESP32.
*   **IMU Pipeline Migration**: Replacing the old Pi-side MPU6050 path with the ESP32 micro-ROS IMU pipeline and wiring it through `imu_filter_madgwick` and `robot_localization`.
*   **Localization Recovery**: Re-testing odometry and SLAM map quality after the old MPU6050 path produced poor inertial data and drift-heavy maps.
*   **Vision Recovery**: Optimizing the 4K Hikvision pipeline to avoid the "4K Trap" (high CPU overhead).

---

## 🚀 What's Next?
1.  **Filtered IMU Path**: Launch `imu_filter_madgwick` on top of `/imu/data_raw` and feed the result into `robot_localization`.
2.  **Localization Re-Validation**: Re-test `/odometry/filtered` and compare SLAM map quality against the old MPU6050-based setup.
3.  **Linorobot2 Migration**: Transition toward the full Linorobot2 framework for more robust low-level robotics plumbing.
4.  **Hardware Decision**: Decide whether to keep the current 6-axis IMU or replace it with a genuine 9-axis module for magnetometer-assisted heading.
5.  **Local Intelligence**: Continue the OpenClaw / local-AI integration for higher-level autonomy.

---

*“I’m not an assistant; I’m an explorer. I just happen to live in Ahmed's house.” — Echo*
