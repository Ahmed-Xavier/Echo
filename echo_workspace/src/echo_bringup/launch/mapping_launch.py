from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration


def full_mapping_command():
    return r"""
set -e

source ~/echo_runtime/bin/echo_env.sh

LOG_DIR=~/echo_runtime/logs
mkdir -p "$LOG_DIR"

ESP32_PORT="/dev/serial/by-path/platform-xhci-hcd.1-usb-0:1:1.0-port0"
ESP32_BAUD="115200"

YDLIDAR_SRC="$HOME/.openclaw/workspace/github_echo/echo_workspace/src/ydlidar_ros2_driver"
YDLIDAR_PARAMS="$YDLIDAR_SRC/params/ydlidar.yaml"

cleanup() {
  echo "[mapping] stopping full mapping stack..."
  kill "$MICRO_PID" "$ODOM_PID" "$EKF_PID" "$LIDAR_PID" "$SLAM_PID" 2>/dev/null || true
  wait "$MICRO_PID" "$ODOM_PID" "$EKF_PID" "$LIDAR_PID" "$SLAM_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

wait_for_node() {
  node="$1"
  seconds="$2"
  echo "[mapping] Waiting for ${node}..."

  for i in $(seq 1 "${seconds}"); do
    if ros2 node list 2>/dev/null | grep -qx "${node}"; then
      echo "[mapping] ${node} is alive."
      return 0
    fi
    sleep 1
  done

  echo "[mapping] ERROR: ${node} did not appear in ${seconds}s."
  return 1
}

wait_for_topic() {
  topic="$1"
  seconds="$2"
  echo "[mapping] Waiting for ${topic}..."

  for i in $(seq 1 "${seconds}"); do
    if timeout 3s ros2 topic echo --once "${topic}" >/dev/null 2>&1; then
      echo "[mapping] ${topic} is publishing."
      return 0
    fi
    sleep 1
  done

  echo "[mapping] ERROR: ${topic} did not publish in ${seconds}s."
  return 1
}

echo "[mapping] Killing stale mapping/localization processes..."
pkill -f "micro_ros_agent.*serial" 2>/dev/null || true
pkill -f "esp32_encoder_odometry" 2>/dev/null || true
pkill -f "ekf_node" 2>/dev/null || true
pkill -f "ydlidar_ros2_driver_node" 2>/dev/null || true
pkill -f "static_transform_publisher.*laser_frame" 2>/dev/null || true
pkill -f "slam_toolbox" 2>/dev/null || true
sleep 2

echo "[mapping] Starting micro_ros_agent on ${ESP32_PORT} @ ${ESP32_BAUD}"
ros2 run micro_ros_agent micro_ros_agent serial --dev "$ESP32_PORT" -b "$ESP32_BAUD" -v4 > "$LOG_DIR/mapping_micro_ros_agent.log" 2>&1 &
MICRO_PID=$!

echo "[mapping] Waiting for /esp32_echo_node. Press ESP32 RST/EN now if needed."
wait_for_node /esp32_echo_node 60

echo "[mapping] Starting encoder odometry..."
ros2 run robot_controller esp32_encoder_odometry > "$LOG_DIR/mapping_odom.log" 2>&1 &
ODOM_PID=$!

wait_for_topic /wheel_odom 30

echo "[mapping] Starting EKF..."
ros2 launch echo_bringup ekf_launch.py > "$LOG_DIR/mapping_ekf.log" 2>&1 &
EKF_PID=$!

wait_for_topic /odometry/filtered 30

echo "[mapping] Starting LiDAR..."
ros2 launch "$YDLIDAR_SRC/launch/ydlidar_launch.py" params_file:="$YDLIDAR_PARAMS" > "$LOG_DIR/mapping_ydlidar.log" 2>&1 &
LIDAR_PID=$!

wait_for_topic /scan 40

echo "[mapping] Starting SLAM Toolbox..."
ros2 launch echo_bringup slam_launch.py > "$LOG_DIR/mapping_slam.log" 2>&1 &
SLAM_PID=$!

wait_for_node /slam_toolbox 30

sleep 2
echo "[mapping] Configuring and activating /slam_toolbox..."
ros2 lifecycle set /slam_toolbox configure || true
sleep 1
ros2 lifecycle set /slam_toolbox activate || true

wait_for_topic /map 30

echo "[mapping] FULL MAPPING STACK READY."
echo "[mapping] Topics: /scan /wheel_odom /odometry/filtered /map"
echo "[mapping] Logs are in $LOG_DIR/mapping_*.log"

wait
"""


def start_foxglove_command():
    return r"""
source ~/echo_runtime/bin/echo_env.sh
exec ros2 launch foxglove_bridge foxglove_bridge_launch.xml port:=8765
"""


def generate_launch_description():
    start_foxglove = LaunchConfiguration("start_foxglove")

    mapping_stack = ExecuteProcess(
        cmd=["bash", "-lc", full_mapping_command()],
        output="screen",
    )

    foxglove = ExecuteProcess(
        cmd=["bash", "-lc", start_foxglove_command()],
        output="screen",
        condition=IfCondition(start_foxglove),
    )

    return LaunchDescription([
        DeclareLaunchArgument("start_foxglove", default_value="false"),
        mapping_stack,
        foxglove,
    ])
