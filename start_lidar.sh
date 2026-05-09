#!/bin/bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash

# Launch LiDAR driver in background
ros2 launch ydlidar_ros2_driver ydlidar_launch.py &
LIDAR_PID=$!

# Wait for scan topic to be available
echo "Waiting for LiDAR to start..."
sleep 3

# Launch RViz
rviz2 &

# Wait for ctrl+c
trap "kill $LIDAR_PID; pkill rviz2; exit" SIGINT SIGTERM
wait
