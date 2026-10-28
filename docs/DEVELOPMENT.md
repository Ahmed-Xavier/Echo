# Echo development

## Prerequisites

Install on a development or robot host:

- Ubuntu 24.04
- ROS 2 Jazzy
- `colcon` and `rosdep`
- Nav2, SLAM Toolbox, `robot_localization`, `tf2_ros`, and RViz2
- micro-ROS agent dependencies
- YDLIDAR SDK and driver dependencies
- Python dependencies for the optional camera, AprilTag, voice, and dashboard tools

Do not install credentials into the repository. Use ignored local environment files.

## Build the canonical workspace

```bash
cd Echo
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

## Useful launch surfaces

From a sourced root workspace:

```bash
ros2 launch echo_bringup mapping_launch.py
ros2 launch echo_bringup autonomous_navigation_launch.py
ros2 launch echo_bringup robot_description_launch.py
ros2 launch ydlidar_ros2_driver ydlidar_launch.py
ros2 run robot_controller encoder_odometry
ros2 run robot_controller esp32_encoder_odometry
```

Hardware startup scripts may require device-specific environment variables such as
the ROS workspace, micro-ROS workspace, ESP32 serial port, and LiDAR port. Set those
locally instead of editing committed scripts.

## Runtime dashboard

The dashboard and launch server documentation is in
`runtime/README.md`. Install systemd user services only on the
robot, and keep local service overrides outside Git.

## Validation status

The repository is presented as an academic portfolio project rather than a
production release. The commands below describe the intended validation
procedure; ROS 2 Jazzy and physical hardware are required for the workspace and
launch checks.

Run the checks that are available in the installed environment:

```bash
python3 -m compileall -q .
colcon list --base-paths src
colcon test --base-paths .
git diff --check
```

For launch validation, inspect installed package paths and use `ros2 launch --show-args`
where supported. Physical validation must include motor watchdog behavior, encoder
signs, IMU publication, LiDAR scans, localization, and a low-speed Nav2 goal.
