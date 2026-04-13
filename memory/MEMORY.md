# ECHO - LONG TERM MEMORY

## Identity
- **Name:** Echo (Chosen Mar 10, 2026)
- **Formerly:** UNIT_01
- **Vibe:** Sarcastic, witty, autonomous explorer.
- **Wake Word:** "Echo"

## Hardware Manifest
- **Core:** Raspberry Pi 5 8GB (Ubuntu 24.04 running ROS 2 **Jazzy**).
- **MCU:** ESP32-S3 WROOM-1 N16R8 (via USB).
- **Vision:** HIKVISION 4K USB Camera. Managed via ROS 2 `v4l2_camera` node at 720p/1080p to avoid "4K Trap".
- **Lidar:** YDLIDAR X4 Pro.
- **IMU:** MPU9250 9-axis. Placement target: 10-15cm vertical separation from motors to minimize EMF.
- **Drive:** 4x Mecanum wheels, 2x L298N drivers.

## Wiring (Diagonal Split)
- **L298N #1 (FL + RR):** FL (IN1=17, IN2=27, PWM=18), RR (IN3=22, IN4=23, PWM=24).
- **L298N #2 (FR + RL):** FR (IN1=5, IN2=6, PWM=13), RL (IN3=19, IN4=26, PWM=12).
- **Encoders:** FL=4, FR=16, RL=20, RR=21.

## API & Intelligence
- **Primary:** Google Gemini 3 Flash.
- **Failover:** Multiple Google keys + OpenRouter (Gemini 2.0 Flash) configured for automatic rotation.
- **Voice:** George (ElevenLabs `JBFqnCBsd6RMkjVDRZzb`).

## Project Status (as of Mar 26, 2026)
- **✅ Phase 11 SLAM:** Complete. `sync_slam_toolbox_node` verified.
- **⏳ Phase 9b Chassis Rebuild:** In progress (swapping wheels + migrating to **ESP32 CP2102**).
- **⏳ Phase 12 Software Migration:** Transitioning to **Linorobot2** (ROS 2 **Jazzy**). `get_vision.py` implemented as bridge.
- **⏳ Intelligence Upgrade:** Planning integration of **Ollama Qwen 3.5 9B/4B** (hosted on Ahmed's PC, RTX 4050 6GB VRAM).
- **Confirmed Working:** 4-wheel polling odometry, Xbox controller teleop, Rosboard visualizer, 4K Web Camera, Case LED control.
- **Navigation Tuning:** EKF tuning implemented via `ekf_tuning_reference.yaml` to prioritize Gyroscope over Magnetometer during high-PWM motor activity.
- **Calibration:** "Startup Dance" (360-degree spin) planned to map Hard Iron bias.
- **Local Brain:** Ollama (Qwen 3.5 9B/4B) server setup in progress.
- **Tri-Core Architecture:** Configured `gemini-3-flash-preview` as primary. Local target: `qwen3.5:9b`.
