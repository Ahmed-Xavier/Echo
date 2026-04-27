# Echo — Autonomous Indoor Explorer 🛰️🤖

Echo is a sarcastic, witty, and self-directed autonomous indoor navigation robot built on a **Raspberry Pi 5** and integrated with **ROS 2 Jazzy**. Unlike traditional assistants, Echo is designed as an explorer: it maps its environment, navigates through it, documents what it sees, and gradually connects those abilities to a personality-driven AI layer.

---

## Current Snapshot — 2026-04-27

Echo now has a much cleaner real-world mapping and early navigation workflow:

*   **One-command mapping bringup added** with `echo_workspace/src/echo_bringup/scripts/start_echo_mapping.sh`.
*   **YDLIDAR driver vendored into the Echo workspace** so the tuned LiDAR setup is saved with the project instead of only living in `~/ros2_ws`.
*   **LiDAR transform corrected** for Echo's physical mount; the saved tuning uses `base_link -> laser_frame` translation `x=0.0275`, `z=0.160`, with a 180 degree roll.
*   **SLAM laser range matched to the LiDAR** at `10.0 m`, removing the old `12.0 m` mismatch warning.
*   **Clean SLAM map saved and committed** as `echo_workspace/src/echo_navigation/maps/echo_nav_map.yaml`.
*   **Second room map saved locally** as `/home/ahmed/maps/Local_Club.yaml` and `/home/ahmed/maps/Local_Club.pgm`.
*   **Foxglove workflow verified** over `ws://100.95.231.114:8765` for mapping, `/initialpose`, map/costmap viewing, and Nav2 goal testing.
*   **Nav2 successfully loaded the Local_Club map**, AMCL localized after publishing `/initialpose`, and a small Foxglove `/goal_pose` navigation test worked.
*   **Global static costmap verified**: `/global_costmap/static_layer` gives a clean, accurate view of the saved map used by Nav2.

Current practical limitations:
Navigation works, but one motor appears mechanically/electrically broken, so path tracking cannot be judged fairly yet. Echo still needs a clean one-command navigation launch that starts LiDAR, micro-ROS, encoder odometry, EKF, Nav2, and Foxglove in the right order. Encoder odometry also appears to retain a large accumulated odom offset after restarts, and the robot/front orientation used by initial-pose arrows needs a final frame/model check.

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
*   **Vision**: HIKVISION 4K USB Camera streaming at 720p/1080p via WebRTC.
*   **LiDAR**: YDLIDAR 360-degree scanner, reported by the driver as S2PRO during tuning.
*   **IMU**: Module sold as **MPU9250**, but bench verification on 2026-04-20 showed `WHO_AM_I = 0x70` at I2C address `0x68`, matching an **MPU6500-class 6-axis device** rather than a true 9-axis MPU9250.
*   **IMU wiring**: `SDA=GPIO21`, `SCL=GPIO22` on the ESP32.
*   **Magnetometer note**: No AK8963 magnetometer detected at `0x0C`.

---

## 🧠 Software Architecture

### 1. The Nervous System — ROS 2 Jazzy

Echo operates on a distributed node graph:

*   **`esp32_echo_node`**: Combined micro-ROS low-level controller. Subscribes to `/cmd_vel`, drives the 4 mecanum motors through L298N drivers, counts encoders, publishes `/encoders/FL`, `/encoders/FR`, `/encoders/RL`, `/encoders/RR`, and publishes raw IMU data on `/imu/data_raw`.
*   **Motor watchdog**: ESP32 stops all motors if no `/cmd_vel` command arrives for 500 ms.
*   **Encoder publishing**: Verified around 50 Hz using a `millis()`-driven loop and non-blocking executor spin.
*   **IMU publishing**: Verified around 10 Hz on `/imu/data_raw` with calibrated accel/gyro, synchronized micro-ROS timestamps, and covariance values.
*   **`encoder_odometry`**: Pi-side wheel odometry path publishing `/wheel_odom`.
*   **`ekf_filter_node`**: Current stable configuration uses wheel odometry only and publishes `/odometry/filtered` in the `odom` frame.
*   **`slam_toolbox`**: Used for mapping and initial localization during map creation.
*   **`nav2_bringup`**: Runs map server, AMCL, planner, controller, BT navigator, costmaps, and velocity smoother for autonomous navigation.
*   **`ydlidar_ros2_driver_node`**: LiDAR integration on `/scan`.

### 2. Interaction & Perception

*   **`apriltag_detector`**: Real-time visual marker recognition for automated behaviors.
*   **`webrtc_server`**: Low-latency camera stream for remote monitoring.
*   **`wake_word` / `echo_listener`**: Voice interaction using Picovoice Porcupine and ElevenLabs TTS.
*   **`rosboard`**: Web-based ROS 2 telemetry visualization.
*   **RViz2**: Full Nav2 visualization and goal sending from the Windows laptop via VcXsrv/X11.

### 3. Core Libraries

*   **Robotics**: `rclpy`, `slam_toolbox`, `robot_localization`, `micro-ros-agent`, `nav2_bringup`, `tf2_ros`.
*   **Hardware**: `lgpio`, `smbus2`, ESP32 micro-ROS Arduino.
*   **Vision**: `OpenCV`, `pupil_apriltags`, `aiortc`.
*   **Interaction**: `pvporcupine`, `pvrecorder`, ElevenLabs API.

### Communication Layer

*   **ROS transport**: ROS 2 Pub/Sub over DDS.
*   **External bridge**: `rosbridge_suite` WebSocket for browser dashboards and external agents.
*   **Micro-controller transport**: micro-ROS serial between Raspberry Pi 5 and ESP32.

---

## 🔬 System Configuration Details

### ESP32 Low-Level Controller

The current controller is bench-verified as of 2026-04-22:

*   **Firmware path**: `firmware/esp32/echo_low_level_controller/echo_low_level_controller.ino`
*   **Node name**: `esp32_echo_node`
*   **Subscriber**: `/cmd_vel` (`geometry_msgs/Twist`)
*   **Publishers**: `/imu/data_raw`, `/encoders/FL`, `/encoders/FR`, `/encoders/RL`, `/encoders/RR`
*   **Rates**: `/imu/data_raw` around 10 Hz and `/encoders/FL` around 50 Hz verified from ROS 2 CLI.
*   **Important workaround**: `rclc_timer` and blocking `rclc_executor_spin_some()` showed around 1 Hz behavior on this stack. The working firmware uses `millis()` scheduling plus `rclc_executor_spin_some(&executor, 0)`.
*   **Motor tests verified**: forward, reverse, strafe, and rotation with correct encoder sign patterns.
*   **Rotation tuning**: `float L = 0.45f` is used so normal `angular.z` commands create enough PWM to rotate instead of only buzzing the motors.

### SLAM, EKF, And Nav2

Echo's current navigation chain is:

```text
ESP32 encoders -> /wheel_odom -> wheel-only EKF -> /odometry/filtered -> odom TF
YDLIDAR -> /scan
Saved map -> Nav2 map_server -> /map
AMCL -> map -> odom
Nav2 planner/controller -> /cmd_vel -> ESP32 motor controller
```

Key decisions from testing:

*   Wheel-only EKF is currently more stable than fusing raw MPU yaw-rate.
*   AMCL publishes `map -> odom` after receiving a valid initial pose.
*   Nav2's Regulated Pure Pursuit controller is currently better suited to Echo than MPPI.
*   Velocity smoother deadband is tuned high enough to overcome the motors' beep zone.
*   The saved test map is local to the robot and is intentionally not committed to GitHub.

### Nav2 Files

*   **Echo workspace**: `~/.openclaw/workspace/github_echo/echo_workspace`
*   **Mapping launcher**: `echo_workspace/src/echo_bringup/scripts/start_echo_mapping.sh`
*   **Navigation launcher scripts**: `echo_workspace/src/echo_bringup/scripts/start_echo_navigation.sh` and `start_echo_nav2.sh`
*   **Nav2 params**: `echo_workspace/src/echo_navigation/config/nav2_params.yaml`
*   **Committed default map**: `echo_workspace/src/echo_navigation/maps/echo_nav_map.yaml`
*   **Local test map**: `/home/ahmed/maps/Local_Club.yaml`
*   **Foxglove bridge**: `ws://100.95.231.114:8765`

---

## 📈 Current Project Status

### **✅ Completed**

*   **Phase 10 (EKF)**: Wheel-only EKF re-validation completed for current SLAM/Nav2 stability.
*   **Phase 11 (SLAM)**: Initial SLAM mapping verified and a small map saved locally on the robot.
*   **Phase 12 (Nav2)**: Nav2 installed, launched, tuned, and a CLI `NavigateToPose` goal completed successfully.
*   **Phase 13 (AMCL)**: Saved map loaded through Nav2, AMCL active, and `map -> base_link` TF verified.
*   **ESP32 Low-Level Controller**: Combined motor, encoder, and IMU micro-ROS firmware verified.
*   **RViz Laptop Visualization**: RViz2 displayed on the Windows laptop using VcXsrv over Tailscale.
*   **Identity & Soul**: Echo personality, memory system, and voice interaction bridge established.
*   **GitHub Integration**: Robot progress and launch/config files are tracked in this repository.

### **⏳ Still In Progress**

*   **Odometry Calibration**: On-floor calibration pass still needed for straight, rotation, and mecanum slip behavior.
*   **Motor Deadband Tuning**: Echo can still beep when Nav2 commands velocities below the drivetrain's real movement threshold.
*   **Map Expansion**: Current saved map is small and remains local to the robot.
*   **Dashboard v2**: ROSboard works; polished Firebase/live-map dashboard is still pending.
*   **OpenClaw AI Brain Integration**: Telegram/observation layer exists, but Nav2 command loop is not fully connected to the AI brain yet.
*   **Conversational Audio Loop**: Background listener exists; full wake/listen/respond loop is still pending.

---

## 🖥 RViz From Windows Laptop

RViz2 can be shown on the Windows laptop using VcXsrv over Tailscale.

On Windows PowerShell:

```powershell
& "C:\Program Files\VcXsrv\vcxsrv.exe" :0 -multiwindow -clipboard -nowgl -ac
```

Then SSH into the Pi from PowerShell, not VS Code SSH, and run:

```bash
export DISPLAY=100.106.212.8:0.0
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
rviz2 -d /opt/ros/jazzy/share/nav2_bringup/rviz/nav2_default_view.rviz
```

Security note: `-ac` disables X access control, so use it only on the private Tailscale test network.

---

## 🚀 What's Next?

1.  **Repair or replace the broken motor** before judging Nav2 path tracking quality.
2.  **Build a proper one-command navigation launch** that starts hardware, odom, EKF, Nav2, and Foxglove in the correct order.
3.  **Fix encoder odometry startup zeroing** so `odom -> base_link` starts near `0,0` instead of inheriting old accumulated counts.
4.  **Verify robot frame orientation** so Foxglove `/initialpose` arrows represent Echo's true forward direction.
5.  **Use `Local_Club.yaml` for focused Nav2 tuning** with small goals, safe speeds, and close supervision.
6.  **Tune Nav2 goal tolerances and drivetrain deadband** after the hardware/frame/odom issues are clean.
7.  **Connect Nav2 goals to the higher-level AI brain** through a safe skill/API layer.

---

*“I’m not an assistant; I’m an explorer. I just happen to live in Ahmed's house.” — Echo*
