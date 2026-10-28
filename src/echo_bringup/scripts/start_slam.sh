#!/usr/bin/env bash
set -euo pipefail

ROS_SETUP="${ROS_SETUP:-/opt/ros/jazzy/setup.bash}"
ROS_WS="${ROS_WS:-$HOME/Echo}"
ECHO_WS="${ECHO_WS:-$HOME/Echo}"

source "$ROS_SETUP"
source "$ROS_WS/install/setup.bash"
source "$ECHO_WS/install/setup.bash"

ros2 launch echo_bringup slam_launch.py
