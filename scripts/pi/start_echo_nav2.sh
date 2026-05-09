#!/usr/bin/env bash
set -euo pipefail

ROS_SETUP="${ROS_SETUP:-/opt/ros/jazzy/setup.bash}"
ROS_WS="${ROS_WS:-$HOME/ros2_ws}"
MAP_FILE="${MAP_FILE:-$HOME/maps/echo_test_map.yaml}"
PARAMS_FILE="${PARAMS_FILE:-$ROS_WS/src/robot_controller/nav2_params.yaml}"

source "$ROS_SETUP"
source "$ROS_WS/install/setup.bash"

if [[ ! -f "$MAP_FILE" ]]; then
  echo "ERROR: map file not found: $MAP_FILE"
  exit 1
fi

if [[ ! -f "$PARAMS_FILE" ]]; then
  echo "ERROR: Nav2 params file not found: $PARAMS_FILE"
  exit 1
fi

echo "Starting Echo Nav2"
echo "  Map:    $MAP_FILE"
echo "  Params: $PARAMS_FILE"

ros2 launch nav2_bringup bringup_launch.py \
  map:="$MAP_FILE" \
  params_file:="$PARAMS_FILE" \
  use_sim_time:=False \
  autostart:=True
