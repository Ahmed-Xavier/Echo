# Echo architecture

## Source of truth

`echo_workspace` is the canonical ROS 2 Jazzy source workspace. It contains the
Echo packages, the vendored YDLIDAR driver and micro-ROS agent, robot description,
navigation configuration, maps, and the canonical dashboard runtime files under
`echo_workspace/echo_runtime/`.

`ros2_ws` is a legacy mirror retained in this branch because deployment scripts and
the physical robot may still reference it. It must not be changed or deleted until
the robot is migrated and a live bringup confirms that `echo_workspace` is the only
runtime source.

The root `echo_runtime/` directory is retained as a legacy compatibility surface for
older service and operator deployments. New deployment work should use
`echo_workspace/echo_runtime/`.

## Package responsibilities

| Package | Responsibility |
| --- | --- |
| `echo_bringup` | System launch files and operator startup scripts |
| `echo_description` | URDF/Xacro robot, drivetrain, sensor, and visualization descriptions |
| `echo_navigation` | Nav2, SLAM, EKF-related configuration, maps, and navigation actions |
| `robot_controller` | Python nodes for motor control, encoders, IMU, and odometry |
| `echo_teleop` | Teleoperation nodes and support scripts |
| `echo_perception` | Camera and AprilTag perception support |
| `echo_voice_ai` | Wake-word, voice, and display helper scripts |
| `echo_hardware` | Hardware package placeholder and install surface |
| `ydlidar_ros2_driver` | Vendored YDLIDAR ROS 2 driver |
| `micro_ros_agent` | Vendored micro-ROS agent |

## Runtime data flow

1. The ESP32 micro-ROS node receives `/cmd_vel`, drives the four mecanum motors,
   and publishes encoder and raw IMU data.
2. `robot_controller` converts encoder data into wheel odometry.
3. `robot_localization` publishes filtered odometry and the `odom` transform.
4. YDLIDAR publishes `/scan`.
5. SLAM Toolbox builds maps during mapping, or Nav2 map server and AMCL localize
   against a saved map.
6. Nav2 produces velocity commands for the ESP32.
7. Camera, AprilTag, voice, rosbridge, Foxglove, and dashboard services are
   optional operator-facing layers.

## Deployment layers

- Firmware is built and flashed independently under `firmware/`.
- ROS packages are built with `colcon` from `echo_workspace`.
- `echo_workspace/echo_runtime/systemd/` contains service templates; local service installation
  and environment values stay on the robot.
- Logs, backups, credentials, and generated runtime state are not repository assets.

## Stability boundary

This organization does not change ROS topics, message types, GPIO assignments,
firmware behavior, motor constants, or public launch interfaces. Any future change
to those interfaces should be treated as a robotics behavior change and tested on
the physical platform.
