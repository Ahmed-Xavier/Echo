#!/usr/bin/env bash
set -euo pipefail

ROS_SETUP="${ROS_SETUP:-/opt/ros/jazzy/setup.bash}"
WORKSPACE_DIR="${WORKSPACE_DIR:-$HOME/.openclaw/workspace/github_echo/echo_workspace}"
MAP_FILE="${MAP_FILE:-$WORKSPACE_DIR/src/echo_navigation/maps/echo_nav_map.yaml}"
PARAMS_FILE="${PARAMS_FILE:-$WORKSPACE_DIR/src/echo_navigation/config/nav2_params.yaml}"

source "$ROS_SETUP"
source "$WORKSPACE_DIR/install/setup.bash"

if [[ ! -f "$MAP_FILE" ]]; then
  echo "ERROR: map file not found: $MAP_FILE"
  exit 1
fi

if [[ ! -f "$PARAMS_FILE" ]]; then
  echo "ERROR: Nav2 params file not found: $PARAMS_FILE"
  exit 1
fi

echo "Starting Echo Nav2..."
echo "Workspace: $WORKSPACE_DIR"
echo "Map: $MAP_FILE"
echo "Params: $PARAMS_FILE"

ros2 launch nav2_bringup bringup_launch.py \
  map:="$MAP_FILE" \
  params_file:="$PARAMS_FILE" \
  use_sim_time:=False \
  autostart:=True

