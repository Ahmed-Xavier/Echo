from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration


def slam_only_command():
    return r"""
set -e

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

wait_for_topic /scan 40
wait_for_topic /odometry/filtered 40

echo "[mapping] Starting SLAM only. robot_body and localization must already be running."
exec ros2 launch echo_bringup slam_launch.py
"""


def activate_slam_command():
    return r"""
echo "[mapping] Waiting for /slam_toolbox..."
until ros2 node list | grep -qx "/slam_toolbox"; do
  sleep 1
done

sleep 2
echo "[mapping] Configuring and activating /slam_toolbox..."
ros2 lifecycle set /slam_toolbox configure || true
sleep 1
ros2 lifecycle set /slam_toolbox activate || true
"""


def generate_launch_description():
    start_slam = LaunchConfiguration("start_slam")
    auto_activate_slam = LaunchConfiguration("auto_activate_slam")
    start_foxglove = LaunchConfiguration("start_foxglove")

    slam = ExecuteProcess(
        cmd=["bash", "-lc", slam_only_command()],
        output="screen",
        condition=IfCondition(start_slam),
    )

    activate_slam = ExecuteProcess(
        cmd=["bash", "-lc", activate_slam_command()],
        output="screen",
        condition=IfCondition(auto_activate_slam),
    )

    foxglove = ExecuteProcess(
        cmd=["ros2", "launch", "foxglove_bridge", "foxglove_bridge_launch.xml", "port:=8765"],
        output="screen",
        condition=IfCondition(start_foxglove),
    )

    return LaunchDescription([
        # Kept for compatibility with old scripts/runtime calls. These are no longer used here.
        DeclareLaunchArgument("esp32_port", default_value="/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0"),
        DeclareLaunchArgument("micro_ros_baud", default_value="115200"),
        DeclareLaunchArgument("start_lidar", default_value="false"),
        DeclareLaunchArgument("start_robot_description", default_value="false"),
        DeclareLaunchArgument("start_micro_ros", default_value="false"),
        DeclareLaunchArgument("start_wheel_odom", default_value="false"),
        DeclareLaunchArgument("start_ekf", default_value="false"),

        DeclareLaunchArgument("start_slam", default_value="true"),
        DeclareLaunchArgument("auto_activate_slam", default_value="true"),
        DeclareLaunchArgument("start_foxglove", default_value="false"),

        slam,
        activate_slam,
        foxglove,
    ])
