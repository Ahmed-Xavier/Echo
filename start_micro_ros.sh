#!/bin/bash
trap "echo 'Shutting down micro-ROS agent...'; kill $(jobs -p) 2>/dev/null" EXIT

source /opt/ros/jazzy/setup.bash
source /home/ahmed/microros_ws/install/setup.bash

echo "========================================="
echo "       ECHO: ESP32 micro-ROS Link        "
echo "========================================="
echo "Starting micro_ros_agent on /dev/ttyUSB0..."

# Run agent in the background
ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyUSB0 -b 115200 &

echo ""
echo ">>> HIT THE RESET BUTTON ON THE ESP32 NOW <<<"
echo ""
sleep 4

echo "Listening to /imu/data_raw (Best Effort)..."
echo "Press Ctrl+C to stop both the listener and the agent."
echo "-----------------------------------------"

# Echo the topic in the foreground
ros2 topic echo /imu/data_raw --qos-reliability best_effort
