#!/usr/bin/env bash
set -euo pipefail

ROS_SETUP="${ROS_SETUP:-/opt/ros/jazzy/setup.bash}"
ECHO_WS="${ECHO_WS:-$HOME/Echo}"
RVIZ_CONFIG="${RVIZ_CONFIG:-/opt/ros/jazzy/share/nav2_bringup/rviz/nav2_default_view.rviz}"

source "$ROS_SETUP"
source "$ECHO_WS/install/setup.bash"

exec rviz2 -d "$RVIZ_CONFIG"
