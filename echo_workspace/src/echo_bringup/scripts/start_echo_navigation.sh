#!/usr/bin/env bash
set -euo pipefail

ROS_SETUP="${ROS_SETUP:-/opt/ros/jazzy/setup.bash}"
ROS_WS="${ROS_WS:-$HOME/ros2_ws}"
MAP_FILE="${MAP_FILE:-$HOME/maps/echo_test_map.yaml}"
NAV2_PARAMS="${NAV2_PARAMS:-$ROS_WS/src/robot_controller/nav2_params.yaml}"

source "$ROS_SETUP"
source "$ROS_WS/install/setup.bash"

if [[ ! -f "$MAP_FILE" ]]; then
  echo "ERROR: map file not found: $MAP_FILE"
  exit 1
fi

if [[ ! -f "$NAV2_PARAMS" ]]; then
  echo "ERROR: Nav2 params file not found: $NAV2_PARAMS"
  exit 1
fi

echo "Stopping old Nav2 nodes..."
pkill -f "[n]av2_bringup" 2>/dev/null || true
pkill -f "[n]av2_container" 2>/dev/null || true
pkill -f "[c]omponent_container" 2>/dev/null || true
sleep 2

echo "Starting Echo Nav2"
echo "  Map:    $MAP_FILE"
echo "  Params: $NAV2_PARAMS"

ros2 launch nav2_bringup bringup_launch.py \
  map:="$MAP_FILE" \
  params_file:="$NAV2_PARAMS" \
  use_sim_time:=False \
  autostart:=True
