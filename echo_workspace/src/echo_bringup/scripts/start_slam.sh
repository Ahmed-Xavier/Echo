#!/bin/bash
source ~/ros2_ws/install/setup.bash

ros2 launch robot_controller slam_launch.py &

echo "Waiting for SLAM node to appear..."
until ros2 node list 2>/dev/null | grep -q slam_toolbox; do
    sleep 1
done
echo "SLAM node found! Waiting for it to be ready..."
sleep 3

echo "Configuring SLAM..."
until ros2 lifecycle set /slam_toolbox configure 2>&1 | grep -q "Transitioning successful"; do
    echo "Retrying configure..."
    sleep 2
done

echo "Activating SLAM..."
until ros2 lifecycle set /slam_toolbox activate 2>&1 | grep -q "Transitioning successful"; do
    echo "Retrying activate..."
    sleep 2
done

echo "SLAM active!"
