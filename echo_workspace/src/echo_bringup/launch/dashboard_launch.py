import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    echo_bringup_share = get_package_share_directory("echo_bringup")
    ydlidar_share = get_package_share_directory("ydlidar_ros2_driver")

    map_file = LaunchConfiguration("map")
    esp32_port = LaunchConfiguration("esp32_port")
    micro_ros_baud = LaunchConfiguration("micro_ros_baud")
    camera_index = LaunchConfiguration("camera_index")

    start_micro_ros = LaunchConfiguration("start_micro_ros")
    start_motor = LaunchConfiguration("start_motor")
    start_odom = LaunchConfiguration("start_odom")
    start_ekf = LaunchConfiguration("start_ekf")
    start_lidar = LaunchConfiguration("start_lidar")
    start_map = LaunchConfiguration("start_map")
    start_rosbridge = LaunchConfiguration("start_rosbridge")
    start_foxglove = LaunchConfiguration("start_foxglove")
    start_camera = LaunchConfiguration("start_camera")
    start_apriltag = LaunchConfiguration("start_apriltag")

    micro_ros_agent = Node(
        package="micro_ros_agent",
        executable="micro_ros_agent",
        name="micro_ros_agent",
        output="screen",
        arguments=["serial", "--dev", esp32_port, "-b", micro_ros_baud],
        condition=IfCondition(start_micro_ros),
    )

    motor_controller = TimerAction(
        period=2.0,
        actions=[
            Node(
                package="robot_controller",
                executable="motor_controller",
                name="motor_controller",
                output="screen",
                condition=IfCondition(start_motor),
            )
        ],
    )

    encoder_odometry = TimerAction(
        period=3.0,
        actions=[
            Node(
                package="robot_controller",
                executable="esp32_encoder_odometry",
                name="esp32_encoder_odometry",
                output="screen",
                condition=IfCondition(start_odom),
            )
        ],
    )

    ekf = TimerAction(
        period=4.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(echo_bringup_share, "launch", "ekf_launch.py")
                ),
                condition=IfCondition(start_ekf),
            )
        ],
    )

    ydlidar = TimerAction(
        period=2.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(ydlidar_share, "launch", "ydlidar_launch.py")
                ),
                launch_arguments={
                    "params_file": os.path.join(ydlidar_share, "params", "ydlidar.yaml"),
                }.items(),
                condition=IfCondition(start_lidar),
            )
        ],
    )

    map_server = Node(
        package="nav2_map_server",
        executable="map_server",
        name="map_server",
        output="screen",
        parameters=[{"yaml_filename": map_file}],
        condition=IfCondition(start_map),
    )

    map_lifecycle = TimerAction(
        period=1.0,
        actions=[
            Node(
                package="nav2_lifecycle_manager",
                executable="lifecycle_manager",
                name="lifecycle_manager_dashboard_map",
                output="screen",
                parameters=[
                    {"autostart": True},
                    {"node_names": ["map_server"]},
                ],
                condition=IfCondition(start_map),
            )
        ],
    )

    rosbridge = ExecuteProcess(
        cmd=["ros2", "launch", "rosbridge_server", "rosbridge_websocket_launch.xml"],
        output="screen",
        condition=IfCondition(start_rosbridge),
    )

    foxglove = ExecuteProcess(
        cmd=["ros2", "launch", "foxglove_bridge", "foxglove_bridge_launch.xml"],
        output="screen",
        condition=IfCondition(start_foxglove),
    )

    camera = TimerAction(
        period=2.0,
        actions=[
            Node(
                package="echo_perception",
                executable="camera_publisher.py",
                name="echo_camera_publisher",
                output="screen",
                parameters=[{"camera_index": camera_index}],
                condition=IfCondition(start_camera),
            )
        ],
    )

    apriltag = TimerAction(
        period=4.0,
        actions=[
            Node(
                package="echo_perception",
                executable="apriltag_detector.py",
                name="apriltag_detector",
                output="screen",
                condition=IfCondition(start_apriltag),
            )
        ],
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            "map",
            default_value=os.path.expanduser("~/maps/Local_Club.yaml"),
        ),
        DeclareLaunchArgument(
            "esp32_port",
            default_value="/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0",
        ),
        DeclareLaunchArgument("micro_ros_baud", default_value="115200"),
        DeclareLaunchArgument("camera_index", default_value="8"),

        DeclareLaunchArgument("start_micro_ros", default_value="true"),
        DeclareLaunchArgument("start_motor", default_value="true"),
        DeclareLaunchArgument("start_odom", default_value="true"),
        DeclareLaunchArgument("start_ekf", default_value="true"),
        DeclareLaunchArgument("start_lidar", default_value="true"),
        DeclareLaunchArgument("start_map", default_value="true"),
        DeclareLaunchArgument("start_rosbridge", default_value="true"),
        DeclareLaunchArgument("start_foxglove", default_value="true"),
        DeclareLaunchArgument("start_camera", default_value="true"),
        DeclareLaunchArgument("start_apriltag", default_value="true"),

        micro_ros_agent,
        motor_controller,
        encoder_odometry,
        ekf,
        ydlidar,
        map_server,
        map_lifecycle,
        rosbridge,
        foxglove,
        camera,
        apriltag,
    ])
