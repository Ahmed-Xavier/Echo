#!/usr/bin/env bash
set -eo pipefail

ROS_SETUP="${ROS_SETUP:-/opt/ros/jazzy/setup.bash}"
ROS_WS="${ROS_WS:-$HOME/ros2_ws}"
MICRO_ROS_WS="${MICRO_ROS_WS:-$HOME/microros_ws}"
ECHO_WS="${ECHO_WS:-$HOME/.openclaw/workspace/github_echo/echo_workspace}"
ESP32_PORT="${ESP32_PORT:-/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0}"

source "$ROS_SETUP"

if [[ -f "$ROS_WS/install/setup.bash" ]]; then
  source "$ROS_WS/install/setup.bash"
fi

if [[ -f "$MICRO_ROS_WS/install/setup.bash" ]]; then
  source "$MICRO_ROS_WS/install/setup.bash"
fi

source "$ECHO_WS/install/setup.bash"

echo "Stopping ModemManager so it does not grab the ESP32 serial port..."
sudo systemctl stop ModemManager 2>/dev/null || true

echo "Stopping stale Echo mapping/sim processes..."
pkill -f fake_cmd_vel_odom.py 2>/dev/null || true
pkill -f rviz_cmd_vel_sim.py 2>/dev/null || true
pkill -f foxglove_bridge 2>/dev/null || true
pkill -f sync_slam_toolbox_node 2>/dev/null || true
pkill -f ydlidar_ros2_driver_node 2>/dev/null || true
pkill -f micro_ros_agent 2>/dev/null || true
pkill -f ekf_node 2>/dev/null || true
pkill -f esp32_encoder_odometry 2>/dev/null || true
pkill -f robot_state_publisher 2>/dev/null || true
pkill -f joint_state_publisher 2>/dev/null || true

sleep 1

echo "Starting Echo mapping stack..."
echo "ESP32: $ESP32_PORT"
echo "Foxglove: ws://$(hostname -I | awk '{print $1}'):8765"
echo "If ESP32 topics do not appear, press ESP32 RST/EN once."

exec ros2 launch echo_bringup mapping_launch.py esp32_port:="$ESP32_PORT" "$@"
