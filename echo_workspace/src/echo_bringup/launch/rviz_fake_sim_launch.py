from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
import os


def generate_launch_description():
    model = LaunchConfiguration("model")
    rviz_config = LaunchConfiguration("rviz_config")
    use_sim_time = LaunchConfiguration("use_sim_time")

    default_model = PathJoinSubstitution([
        FindPackageShare("echo_description"),
        "urdf",
        "robots",
        "mecanum.urdf.xacro",
    ])

    default_rviz_config = os.path.join(
        get_package_share_directory("echo_bringup"),
        "config",
        "rviz_fake_sim.rviz",
    )

    robot_description = {
        "robot_description": Command([
            "xacro ",
            model,
        ])
    }

    return LaunchDescription([
        DeclareLaunchArgument(
            "model",
            default_value=default_model,
            description="Absolute path to robot URDF/Xacro file.",
        ),
        DeclareLaunchArgument(
            "rviz_config",
            default_value=default_rviz_config,
            description="RViz config file for fake movement simulation.",
        ),
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="false",
            description="Use simulation time.",
        ),
        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            name="robot_state_publisher",
            output="screen",
            parameters=[
                robot_description,
                {"use_sim_time": use_sim_time},
            ],
        ),
        Node(
            package="echo_teleop",
            executable="rviz_cmd_vel_sim.py",
            name="rviz_cmd_vel_sim",
            output="screen",
            parameters=[
                {"use_sim_time": use_sim_time},
            ],
        ),
        Node(
            package="rviz2",
            executable="rviz2",
            name="rviz2",
            output="screen",
            arguments=["-d", rviz_config],
            parameters=[{"use_sim_time": use_sim_time}],
        ),
    ])
