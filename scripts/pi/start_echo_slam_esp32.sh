#!/usr/bin/env bash
set -u

ROS_DISTRO_NAME="${ROS_DISTRO_NAME:-jazzy}"
ROS_SETUP="/opt/ros/${ROS_DISTRO_NAME}/setup.bash"
ROS_WS="/home/ahmed/ros2_ws"
MICRO_ROS_WS="/home/ahmed/microros_ws"

ESP32_PORT="${ESP32_PORT:-/dev/ttyUSB0}"
LIDAR_PORT="${LIDAR_PORT:-/dev/ttyUSB1}"
ESP32_BAUD="${ESP32_BAUD:-115200}"

LOG_DIR="/tmp/echo_slam_esp32_logs"
mkdir -p "$LOG_DIR"

PIDS=()

source "$ROS_SETUP"
source "$ROS_WS/install/setup.bash"

cleanup() {
  echo
  echo "Stopping Echo SLAM stack..."
  for pid in "${PIDS[@]:-}"; do
    kill "$pid" 2>/dev/null || true
  done

  pkill -f "micro_ros_agent.*serial" 2>/dev/null || true
  pkill -f "esp32_encoder_odometry" 2>/dev/null || true
  pkill -f "ekf_node" 2>/dev/null || true
  pkill -f "ydlidar_ros2_driver_node" 2>/dev/null || true
  pkill -f "ydlidar_launch.py" 2>/dev/null || true
  pkill -f "static_tf_pub_laser" 2>/dev/null || true
  pkill -f "slam_toolbox" 2>/dev/null || true
  pkill -f "rosboard_node" 2>/dev/null || true
  pkill -f "joy_node" 2>/dev/null || true
  pkill -f "teleop_node" 2>/dev/null || true

  ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
    "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}" \
    >/dev/null 2>&1 || true

  echo "Stopped."
}
trap cleanup EXIT INT TERM

start_bg() {
  local name="$1"
  shift
  echo "Starting $name..."
  bash -lc "$*" >"$LOG_DIR/${name}.log" 2>&1 &
  local pid=$!
  PIDS+=("$pid")
  echo "  pid=$pid log=$LOG_DIR/${name}.log"
}

wait_for_topic() {
  local topic="$1"
  local timeout_s="$2"
  local start
  start="$(date +%s)"

  while true; do
    if ros2 topic list 2>/dev/null | grep -qx "$topic"; then
      return 0
    fi

    if (( "$(date +%s)" - start >= timeout_s )); then
      return 1
    fi

    sleep 1
  done
}

wait_for_node() {
  local node="$1"
  local timeout_s="$2"
  local start
  start="$(date +%s)"

  while true; do
    if ros2 node list 2>/dev/null | grep -qx "$node"; then
      return 0
    fi

    if (( "$(date +%s)" - start >= timeout_s )); then
      return 1
    fi

    sleep 1
  done
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "       ECHO ESP32 SLAM STACK"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "ESP32 port: $ESP32_PORT @ $ESP32_BAUD"
echo "LiDAR port: $LIDAR_PORT @ 128000"
echo "Logs: $LOG_DIR"
echo

echo "Stopping old conflicting nodes..."
pkill -f "motor_controller" 2>/dev/null || true
pkill -f "encoder_odometry" 2>/dev/null || true
pkill -f "imu_node" 2>/dev/null || true
pkill -f "micro_ros_agent.*serial" 2>/dev/null || true
pkill -f "ydlidar_ros2_driver_node" 2>/dev/null || true
pkill -f "ydlidar_launch.py" 2>/dev/null || true
pkill -f "slam_toolbox" 2>/dev/null || true
pkill -f "ekf_node" 2>/dev/null || true
pkill -f "rosboard_node" 2>/dev/null || true
pkill -f "joy_node" 2>/dev/null || true
pkill -f "teleop_node" 2>/dev/null || true
sleep 2

start_bg "micro_ros_agent" \
  "source '$ROS_SETUP'; source '$MICRO_ROS_WS/install/setup.bash'; ros2 run micro_ros_agent micro_ros_agent serial --dev '$ESP32_PORT' -b '$ESP32_BAUD'"

echo "Waiting for ESP32 topics..."
if ! wait_for_topic "/imu/data_raw" 15; then
  echo
  echo "ESP32 topics not visible yet. Press the ESP32 EN/RST button now."
  echo "Waiting up to 45 seconds more..."
  if ! wait_for_topic "/imu/data_raw" 45; then
    echo "ERROR: ESP32 did not publish /imu/data_raw. Check $LOG_DIR/micro_ros_agent.log"
    exit 1
  fi
fi
echo "ESP32 online."

start_bg "esp32_encoder_odometry" \
  "source '$ROS_SETUP'; source '$ROS_WS/install/setup.bash'; ros2 run robot_controller esp32_encoder_odometry"
wait_for_topic "/wheel_odom" 10 || {
  echo "ERROR: /wheel_odom did not appear. Check $LOG_DIR/esp32_encoder_odometry.log"
  exit 1
}

start_bg "ekf" \
  "source '$ROS_SETUP'; source '$ROS_WS/install/setup.bash'; ros2 run robot_localization ekf_node --ros-args --params-file '$ROS_WS/src/robot_controller/ekf.yaml' -r /imu/data:=/imu/data_raw"
wait_for_topic "/odometry/filtered" 10 || {
  echo "ERROR: /odometry/filtered did not appear. Check $LOG_DIR/ekf.log"
  exit 1
}

sed "s#port: /dev/ttyUSB0#port: ${LIDAR_PORT}#" \
  "$ROS_WS/src/ydlidar_ros2_driver/params/ydlidar.yaml" \
  >/tmp/echo_ydlidar.yaml

start_bg "ydlidar" \
  "source '$ROS_SETUP'; source '$ROS_WS/install/setup.bash'; ros2 launch ydlidar_ros2_driver ydlidar_launch.py params_file:=/tmp/echo_ydlidar.yaml"
wait_for_topic "/scan" 20 || {
  echo "ERROR: /scan did not appear. Check $LOG_DIR/ydlidar.log"
  exit 1
}

start_bg "slam_toolbox" \
  "source '$ROS_SETUP'; source '$ROS_WS/install/setup.bash'; ros2 launch robot_controller slam_launch.py"

echo "Waiting for SLAM toolbox..."
wait_for_node "/slam_toolbox" 20 || {
  echo "ERROR: /slam_toolbox did not appear. Check $LOG_DIR/slam_toolbox.log"
  exit 1
}

sleep 3
echo "Configuring SLAM..."
until ros2 lifecycle set /slam_toolbox configure 2>&1 | grep -q "Transitioning successful"; do
  echo "  retrying configure..."
  sleep 2
done

echo "Activating SLAM..."
until ros2 lifecycle set /slam_toolbox activate 2>&1 | grep -q "Transitioning successful"; do
  echo "  retrying activate..."
  sleep 2
done

start_bg "rosboard" \
  "source '$ROS_SETUP'; source '$ROS_WS/install/setup.bash'; ros2 run rosboard rosboard_node"

start_bg "joy_node" \
  "source '$ROS_SETUP'; source '$ROS_WS/install/setup.bash'; ros2 run joy joy_node"

start_bg "teleop_twist_joy" \
  "source '$ROS_SETUP'; source '$ROS_WS/install/setup.bash'; ros2 run teleop_twist_joy teleop_node --ros-args -p enable_button:=6 -p axis_linear.x:=1 -p axis_linear.y:=0 -p axis_angular.yaw:=3 -p scale_linear.x:=0.3 -p scale_linear.y:=0.3 -p scale_angular.yaw:=0.3"

IP="$(hostname -I | awk '{print $1}')"

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ECHO SLAM STACK IS ONLINE"
echo "  Rosboard: http://$IP:8888"
echo "  SLAM: /map + /map_metadata"
echo "  Odometry: /wheel_odom + /odometry/filtered"
echo "  Xbox: hold LB to enable teleop"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo
echo "Useful checks:"
echo "  ros2 topic hz /scan"
echo "  ros2 topic hz /odometry/filtered"
echo "  ros2 topic echo --once /map_metadata"
echo
echo "Keep this terminal open. Press Ctrl+C here to stop the stack."

wait
