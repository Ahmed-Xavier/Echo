# Echo — Autonomous Indoor Explorer 🛰️🤖

Echo is a sarcastic, witty, and self-directed autonomous indoor navigation robot built on a **Raspberry Pi 5** and integrated with **ROS 2 Jazzy**. Unlike traditional assistants, Echo is designed as an explorer: it maps its environment, navigates through it, documents what it sees, and gradually connects those abilities to a personality-driven AI layer.

---

## Current Snapshot — 2026-04-23

Echo now has a working ROS 2 navigation stack:

*   **SLAM map created** with `slam_toolbox` and saved locally on the robot at `/home/ahmed/maps/echo_test_map.yaml`.
*   **Wheel-only EKF path validated** for stability: `/wheel_odom` publishes around 50 Hz and `/odometry/filtered` publishes around 30 Hz.
*   **Raw IMU yaw-rate removed from EKF** because it caused false rotation during SLAM/Nav2 testing.
*   **Nav2 installed and running** on ROS 2 Jazzy with `map_server`, `AMCL`, planner, controller, BT navigator, and velocity smoother active.
*   **AMCL localization verified** with `map -> base_link` TF after setting the initial pose.
*   **First autonomous Nav2 drive succeeded** using a CLI `NavigateToPose` goal.
*   **Regulated Pure Pursuit selected** over MPPI because it behaved better with Echo's motor deadband.
*   **RViz2 Nav2 workflow verified** from a Windows laptop using VcXsrv/X11 over Tailscale.

Current practical limitation: Echo can still beep or hesitate when Nav2 sends commands below the drivetrain's real motor deadband, especially for turn-heavy or tiny correction goals. Best testing is currently small forward goals in known free map space.

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
*   **LiDAR**: YDLIDAR X4 Pro, 360-degree laser scanner.
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

*   **Repo params**: `ros2_ws/src/robot_controller/nav2_params.yaml`
*   **Live params on Pi**: `/home/ahmed/ros2_ws/src/robot_controller/nav2_params.yaml`
*   **Repo launcher**: `scripts/pi/start_echo_navigation.sh`
*   **Live launcher on Pi**: `/home/ahmed/start_echo_navigation.sh`
*   **Default map path**: `/home/ahmed/maps/echo_test_map.yaml`

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

1.  **Run careful Nav2 sessions** with `/home/ahmed/start_echo_navigation.sh` after the base odom/LiDAR stack is running.
2.  **Calibrate odometry** with short straight and rotation tests, then adjust wheel geometry/constants.
3.  **Expand the map** in a controlled area with cable management solved.
4.  **Tune drivetrain deadband/PWM mapping** so Nav2 can command smoother low-speed corrections without beeping.
5.  **Connect Nav2 goals to the higher-level AI brain** through a safe skill/API layer.
6.  **Build a browser click-to-goal dashboard** or evaluate Foxglove as a cleaner operator UI.

---

*“I’m not an assistant; I’m an explorer. I just happen to live in Ahmed's house.” — Echo*
