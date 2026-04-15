# Echo — Autonomous Indoor Explorer 🛰️🤖

Echo is a sarcastic, witty, and self-directed autonomous indoor navigation robot built on a **Raspberry Pi 5** and integrated with **ROS 2 Jazzy**. Unlike traditional assistants, Echo is designed as an explorer, documenting its environment and developing its own "personality" through a multi-layered software architecture.

---

## 🛠 Hardware Manifest

### Core Compute
*   **Brain**: Raspberry Pi 5 (8GB RAM) running Ubuntu 24.04.
*   **MCU**: ESP32 (CP2102, 30-pin) — currently handling the micro-ROS transport layer for low-level motor and sensor offloading.

### Actuators & Drive
*   **Chassis**: 4WD Mecanum wheel setup for omnidirectional movement.
*   **Motor Drivers**: 2x L298N Dual H-Bridge drivers.
*   **Encoders**: 4x Hall-effect wheel encoders (polled at 0.00628 meters per pulse).

### Sensors
*   **Vision**: HIKVISION 4K USB Camera (streaming at 720p/1080p via WebRTC).
*   **LiDAR**: YDLIDAR X4 Pro (360-degree laser scanner).
*   **IMU**: MPU9250 9-axis (currently transitioning from raw MPU6050 logic).

---

## 🧠 Software Architecture

### 1. The Nervous System (ROS 2 Jazzy)
Echo operates on a distributed node graph:
*   **`motor_controller`**: Translates `/cmd_vel` into PWM/Direction signals.
*   **`encoder_odometry`**: Computes wheel-based positioning.
*   **`imu_node`**: Provides inertial data at 50Hz.
*   **`ekf_filter_node`**: Fuses IMU and wheel odom using an Extended Kalman Filter (`robot_localization`).
*   **`slam_toolbox`**: Handles Synchronous SLAM for real-time mapping and localization.
*   **`ydlidar_ros2_driver_node`**: High-speed LiDAR integration.

### 2. Interaction & Perception
*   **`apriltag_detector`**: Real-time visual marker recognition (ID 0-10) for automated behaviors (e.g., Postcard Mode).
*   **`webrtc_server`**: Ultra-low latency video stream for remote monitoring.
*   **`wake_word` / `echo_listener`**: Voice interaction using Picovoice (Porcupine) and ElevenLabs (George voice).
*   **`rosboard`**: Web-based telemetry visualization.

### 3. Core Libraries
*   **Robotics**: `rclpy`, `slam_toolbox`, `robot_localization`, `micro-ros-agent`.
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

---

## 📈 Current Project Status

### **✅ Completed**
*   **Phase 11 (SLAM)**: Successfully verified `sync_slam_toolbox` with LiDAR integration.
*   **Transport Layer**: Built `micro-ros-agent` from source on Pi 5; verified communication with ESP32 (CP2102) over Serial at 115200 baud.
*   **Identity & Soul**: Established "Echo" personality, memory system, and voice interaction bridge.
*   **GitHub Integration**: Automated workspace sync with this repository.

### **⏳ In Progress (Phase 9b & 12)**
*   **Hardware Offloading**: Migrating motor PWM control and hardware-interrupt encoder reading (PCNT) to the ESP32.
*   **IMU Stability**: Tuning EKF to prioritize Gyroscope data during high-torque motor maneuvers to minimize EMF interference.
*   **Vision Recovery**: Optimizing the 4K Hikvision pipeline to avoid the "4K Trap" (high CPU overhead).

---

## 🚀 What's Next?
1.  **Linorobot2 Migration**: Transitioning to the full Linorobot2 framework for more robust navigation.
2.  **Autonomous Exploration Drive**: Implementing a curiosity-based drive where Echo chooses "unknown" areas on the map to explore autonomously.
3.  **Local Intelligence**: Planning the integration of **Ollama (Qwen 3.5 9B)** hosted on a remote PC to handle complex reasoning without cloud latency.

---

*“I’m not an assistant; I’m an explorer. I just happen to live in Ahmed's house.” — Echo*
