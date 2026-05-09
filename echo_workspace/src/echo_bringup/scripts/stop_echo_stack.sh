#!/usr/bin/env bash
set -euo pipefail

ROS_SETUP="${ROS_SETUP:-/opt/ros/jazzy/setup.bash}"
ROS_WS="${ROS_WS:-$HOME/ros2_ws}"
ECHO_WS="${ECHO_WS:-$HOME/.openclaw/workspace/github_echo/echo_workspace}"

source "$ROS_SETUP"
if [[ -f "$ROS_WS/install/setup.bash" ]]; then
  source "$ROS_WS/install/setup.bash"
fi
if [[ -f "$ECHO_WS/install/setup.bash" ]]; then
  source "$ECHO_WS/install/setup.bash"
fi

echo "Publishing zero velocity..."
timeout 3s ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}" || true

echo "Stopping ROS 2 robot stack processes..."
pkill -f "nav2" 2>/dev/null || true
pkill -f "component_container" 2>/dev/null || true
pkill -f "slam_toolbox" 2>/dev/null || true
pkill -f "ydlidar" 2>/dev/null || true
pkill -f "micro_ros_agent" 2>/dev/null || true
pkill -f "esp32_encoder_odometry" 2>/dev/null || true
pkill -f "robot_localization" 2>/dev/null || true
pkill -f "ekf_node" 2>/dev/null || true
pkill -f "rosboard" 2>/dev/null || true
pkill -f "joy_node" 2>/dev/null || true
pkill -f "teleop_node" 2>/dev/null || true
pkill -f "static_transform_publisher" 2>/dev/null || true

echo "Echo stack stop request sent."

