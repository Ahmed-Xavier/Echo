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
- **GitHub Sync**: Successfully pushed Echo's workspace (core, bridge, docs, memory) to `https://github.com/Ahmed-Xavier/Echo.git` using a Personal Access Token on Apr 15, 2026.
- **GitHub Token**: Saved in local workspace configuration for future syncs.
- **Phase 9b micro-ROS**: Transport layer verified (Pi 5 to ESP32-S3 over USB). Agent running on `/dev/ttyUSB0`.
- **Phase 12 Migration**: Prepared to transition all motor/encoder/IMU logic to ESP32 firmware.
