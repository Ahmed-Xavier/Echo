#!/usr/bin/env bash
set -euo pipefail

ROS_SETUP="${ROS_SETUP:-/opt/ros/jazzy/setup.bash}"
WORKSPACE_DIR="${WORKSPACE_DIR:-$HOME/.openclaw/workspace/github_echo/echo_workspace}"
MAP_FILE="${MAP_FILE:-$WORKSPACE_DIR/src/echo_navigation/maps/echo_test_map.yaml}"
NAV2_PARAMS="${NAV2_PARAMS:-$WORKSPACE_DIR/src/echo_navigation/config/nav2_params.yaml}"

source "$ROS_SETUP"
source "$WORKSPACE_DIR/install/setup.bash"

if [[ ! -f "$MAP_FILE" ]]; then
  echo "ERROR: map file not found: $MAP_FILE"
  exit 1
fi

if [[ ! -f "$NAV2_PARAMS" ]]; then
  echo "ERROR: Nav2 params file not found: $NAV2_PARAMS"
  exit 1
fi

echo "Starting Echo navigation stack..."
echo "Workspace: $WORKSPACE_DIR"
echo "Map: $MAP_FILE"
echo "Params: $NAV2_PARAMS"

ros2 launch nav2_bringup bringup_launch.py \
  map:="$MAP_FILE" \
  params_file:="$NAV2_PARAMS" \
  use_sim_time:=False \
  autostart:=True

