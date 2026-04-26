from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def include_py_launch(package_name, launch_file, condition=None):
    return IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare(package_name), "launch", launch_file])
        ),
        condition=condition,
    )


def wait_for_topic(topic_name, seconds=20):
    return (
        f"echo 'Waiting for {topic_name}...'; "
        f"for i in $(seq 1 {seconds}); do "
        f"  if ros2 topic list | grep -qx '{topic_name}'; then "
        f"    timeout 3s ros2 topic echo {topic_name} --once >/dev/null 2>&1 && exit 0; "
        f"  fi; "
        f"  sleep 1; "
        f"done; "
        f"echo 'WARNING: {topic_name} did not produce data before timeout'; "
        f"exit 0"
    )


def generate_launch_description():
    esp32_port = LaunchConfiguration("esp32_port")
    micro_ros_baud = LaunchConfiguration("micro_ros_baud")

    start_lidar = LaunchConfiguration("start_lidar")
    start_robot_description = LaunchConfiguration("start_robot_description")
    start_micro_ros = LaunchConfiguration("start_micro_ros")
    start_wheel_odom = LaunchConfiguration("start_wheel_odom")
    start_ekf = LaunchConfiguration("start_ekf")
    start_slam = LaunchConfiguration("start_slam")
    auto_activate_slam = LaunchConfiguration("auto_activate_slam")
    start_foxglove = LaunchConfiguration("start_foxglove")

    lidar = include_py_launch(
        "ydlidar_ros2_driver",
        "ydlidar_launch.py",
        condition=IfCondition(start_lidar),
    )

    robot_description = include_py_launch(
        "echo_bringup",
        "robot_description_launch.py",
        condition=IfCondition(start_robot_description),
    )

    micro_ros_agent = Node(
        package="micro_ros_agent",
        executable="micro_ros_agent",
        name="micro_ros_agent",
        output="screen",
        arguments=["serial", "--dev", esp32_port, "-b", micro_ros_baud],
        condition=IfCondition(start_micro_ros),
    )

    wait_for_esp32_and_lidar = TimerAction(
        period=5.0,
        actions=[
            ExecuteProcess(
                cmd=[
                    "bash",
                    "-lc",
                    (
                        wait_for_topic("/scan", 25)
                        + "; "
                        + wait_for_topic("/encoders/FL", 60)
                        + "; "
                        + wait_for_topic("/imu/data_raw", 60)
                        + "; "
                        + "echo 'Required sensor topics are available.'"
                    ),
                ],
                output="screen",
            )
        ],
    )

    wheel_odom = TimerAction(
        period=70.0,
        actions=[
            Node(
                package="robot_controller",
                executable="esp32_encoder_odometry",
                name="esp32_encoder_odometry",
                output="screen",
                condition=IfCondition(start_wheel_odom),
            )
        ],
    )

    ekf = TimerAction(
        period=76.0,
        actions=[
            include_py_launch(
                "echo_bringup",
                "ekf_launch.py",
                condition=IfCondition(start_ekf),
            )
        ],
    )

    slam = TimerAction(
        period=86.0,
        actions=[
            include_py_launch(
                "echo_bringup",
                "slam_launch.py",
                condition=IfCondition(start_slam),
            )
        ],
    )

    activate_slam = TimerAction(
        period=96.0,
        actions=[
            ExecuteProcess(
                cmd=[
                    "bash",
                    "-lc",
                    (
                        "echo 'Waiting for SLAM inputs before activation...'; "
                        "until ros2 node list | grep -qx '/slam_toolbox'; do sleep 1; done; "
                        "until ros2 topic list | grep -qx '/scan'; do sleep 1; done; "
                        "until ros2 topic list | grep -qx '/odometry/filtered'; do sleep 1; done; "
                        "sleep 5; "
                        "ros2 lifecycle set /slam_toolbox configure || true; "
                        "sleep 2; "
                        "ros2 lifecycle set /slam_toolbox activate || true"
                    ),
                ],
                output="screen",
                condition=IfCondition(auto_activate_slam),
            )
        ],
    )

    foxglove = TimerAction(
        period=115.0,
        actions=[
            ExecuteProcess(
                cmd=["ros2", "launch", "foxglove_bridge", "foxglove_bridge_launch.xml", "port:=8765"],
                output="screen",
                condition=IfCondition(start_foxglove),
            )
        ],
    )

    return LaunchDescription([
        DeclareLaunchArgument("esp32_port", default_value="/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0"),
        DeclareLaunchArgument("micro_ros_baud", default_value="115200"),
        DeclareLaunchArgument("start_lidar", default_value="true"),
        DeclareLaunchArgument("start_robot_description", default_value="true"),
        DeclareLaunchArgument("start_micro_ros", default_value="true"),
        DeclareLaunchArgument("start_wheel_odom", default_value="true"),
        DeclareLaunchArgument("start_ekf", default_value="true"),
        DeclareLaunchArgument("start_slam", default_value="true"),
        DeclareLaunchArgument("auto_activate_slam", default_value="true"),
        DeclareLaunchArgument("start_foxglove", default_value="true"),
        lidar,
        robot_description,
        micro_ros_agent,
        wait_for_esp32_and_lidar,
        wheel_odom,
        ekf,
        slam,
        activate_slam,
        foxglove,
    ])
