#!/bin/bash

source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "       ECHO — STARTING UP 🤖"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Kill any previous instances
pkill -f ydlidar 2>/dev/null
pkill -f rosbridge 2>/dev/null
pkill -f apriltag_detector 2>/dev/null
pkill -f webrtc_server 2>/dev/null
pkill -f motor_controller 2>/dev/null
pkill -f encoder_odometry 2>/dev/null
pkill -f imu_node 2>/dev/null
pkill -f ekf_node 2>/dev/null
pkill -f slam_toolbox 2>/dev/null
pkill -f rosboard 2>/dev/null
pkill -f joy_node 2>/dev/null
pkill -f teleop_node 2>/dev/null
sleep 2

echo "[1/9] Starting LiDAR..."
ros2 launch ydlidar_ros2_driver ydlidar_launch.py &
sleep 3

echo "[2/9] Starting IMU..."
ros2 run robot_controller imu_node &
sleep 4

echo "[3/9] Starting encoders + motors..."
ros2 run robot_controller encoder_odometry &
ros2 run robot_controller motor_controller &
sleep 2

echo "[4/9] Starting EKF sensor fusion..."
ros2 launch robot_controller ekf_launch.py &
sleep 3

echo "[5/9] Starting SLAM..."
bash ~/start_slam.sh &
sleep 18

echo "[6/9] Starting rosbridge..."
ros2 launch rosbridge_server rosbridge_websocket_launch.xml &
sleep 2

echo "[7/9] Starting AprilTag + WebRTC..."
python3 ~/apriltag_detector.py &
python3 ~/webrtc_server.py &
sleep 2

echo "[8/9] Starting rosboard..."
ros2 run rosboard rosboard_node &
sleep 1

echo "[9/9] Starting controller..."
ros2 run joy joy_node &
ros2 run teleop_twist_joy teleop_node --ros-args \
  -p enable_button:=6 \
  -p axis_linear.x:=1 \
  -p axis_linear.y:=0 \
  -p axis_angular.yaw:=3 \
  -p scale_linear.x:=0.3 \
  -p scale_linear.y:=0.3 \
  -p scale_angular.yaw:=0.3 &

IP=$(hostname -I | awk '{print $1}')
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ECHO IS ONLINE 🛰️"
echo "  Rosbridge:  ws://$IP:9090"
echo "  WebRTC:     http://$IP:8081"
echo "  Rosboard:   http://$IP:8888"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

trap "echo 'Shutting down Echo...'; pkill -f ydlidar; pkill -f rosbridge; pkill -f apriltag; pkill -f webrtc; pkill -f motor_controller; pkill -f encoder_odometry; pkill -f imu_node; pkill -f ekf_node; pkill -f slam_toolbox; pkill -f rosboard; pkill -f joy_node; pkill -f teleop_node" EXIT
wait
