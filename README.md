# Echo

Echo is a Raspberry Pi 5 and ESP32 indoor mobile robot built around ROS 2 Jazzy.
It combines mecanum drive control, wheel odometry, IMU and LiDAR sensing, SLAM,
Nav2 navigation, AprilTag perception, voice interaction, and a browser dashboard.

## Architecture

The authoritative ROS 2 source workspace is `echo_workspace`.

```text
ESP32 micro-ROS controller
  -> encoders and raw IMU
  -> robot_controller wheel odometry
  -> robot_localization EKF
  -> SLAM or AMCL + Nav2
  -> /cmd_vel
  -> ESP32 mecanum motor controller

YDLIDAR -> /scan
USB camera -> AprilTag perception -> optional navigation actions
ROS bridge and dashboard -> browser and remote operator tools
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for package ownership and data
flow, and [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for setup and validation.

## Repository layout

| Path | Purpose |
| --- | --- |
| `echo_workspace/` | Canonical ROS 2 Jazzy workspace and runtime deployment files |
| `echo_workspace/src/` | Echo packages and vendored ROS 2 dependencies |
| `firmware/` | ESP32 low-level controller firmware |
| `echo_workspace/echo_runtime/` | Canonical dashboard, launch server, systemd templates, and runtime tools |
| `echo_runtime/` | Legacy runtime compatibility files retained until deployment migration is verified |
| `scripts/` | Operator utilities retained for compatibility |
| `docs/` | Architecture, development, security, and operator documentation |
| `ros2_ws/` | Legacy workspace mirror retained until robot deployment migration is verified |

## Hardware

- Raspberry Pi 5 running Ubuntu 24.04 and ROS 2 Jazzy
- ESP32 running the combined micro-ROS low-level controller
- Four-wheel mecanum chassis with L298N motor drivers and Hall encoders
- YDLIDAR 360-degree LiDAR
- MPU6500-class IMU module
- USB camera for AprilTags and video streaming

Hardware behavior, ROS topic names, GPIO assignments, and firmware interfaces are
preserved by this organization work.

## Implemented components

- ESP32 motor, encoder, and raw IMU publishing
- Wheel odometry and wheel-only EKF localization
- LiDAR-driven SLAM and saved-map Nav2 navigation
- Mecanum Nav2 tuning and named-place navigation
- AprilTag detection and action routing
- ROS bridge, Foxglove, and local dashboard support
- Voice wake-word and ElevenLabs text-to-speech integration when local credentials are configured

These capabilities are represented in the repository; ROS 2 builds, full launch
validation, and physical robot tests have not been completed in the current
development environment.

## Experimental or planned

- AprilTag action debouncing and robust Nav2 busy-state handling
- Higher-level AI skill integration for navigation
- Cloud orchestration and remote control
- Final robot-frame and odometry-offset verification

## Security

Credentials must be supplied through the environment and never committed. Start with
the examples in `echo_runtime/voice/.env.example`; see [docs/SECURITY.md](docs/SECURITY.md)
for the exposure assessment and rotation checklist.

## License and dependencies

Package-level licenses and dependencies are declared in the ROS manifests. Vendored
third-party packages retain their upstream documentation and licensing files. The
development environment must provide ROS 2 Jazzy, `colcon`, Nav2, SLAM Toolbox,
`robot_localization`, micro-ROS, YDLIDAR dependencies, and the Python packages used
by the optional perception and voice tools.
