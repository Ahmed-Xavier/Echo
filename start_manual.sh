#!/bin/bash

source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "       ECHO — MANUAL CONTROL 🎮"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

pkill -f motor_controller 2>/dev/null
pkill -f encoder_odometry 2>/dev/null
pkill -f imu_node 2>/dev/null
pkill -f joy_node 2>/dev/null
pkill -f teleop_node 2>/dev/null
sleep 2

echo "[1/3] Starting motors..."
ros2 run robot_controller motor_controller &
sleep 2

echo "[2/3] Starting controller..."
ros2 run joy joy_node &
sleep 1

echo "[3/3] Starting teleop..."
ros2 run teleop_twist_joy teleop_node --ros-args \
  -p enable_button:=6 \
  -p axis_linear.x:=1 \
  -p axis_linear.y:=0 \
  -p axis_angular.yaw:=3 \
  -p scale_linear.x:=0.5 \
  -p scale_linear.y:=0.5 \
  -p scale_angular.yaw:=0.5

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  READY — Hold LB to drive 🎮"
echo "  Left stick: move   Right stick: rotate"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

trap "pkill -f motor_controller; pkill -f joy_node; pkill -f teleop_node" EXIT
wait
