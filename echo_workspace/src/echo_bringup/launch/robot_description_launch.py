from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    model = LaunchConfiguration("model")
    use_sim_time = LaunchConfiguration("use_sim_time")

    default_model = PathJoinSubstitution([
        FindPackageShare("echo_description"),
        "urdf",
        "robots",
        "mecanum.urdf.xacro",
    ])

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
            "use_sim_time",
            default_value="false",
            description="Use simulation time.",
        ),
        Node(
            package="joint_state_publisher",
            executable="joint_state_publisher",
            name="joint_state_publisher",
            output="screen",
            parameters=[
                robot_description,
                {"use_sim_time": use_sim_time},
            ],
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
    ])

