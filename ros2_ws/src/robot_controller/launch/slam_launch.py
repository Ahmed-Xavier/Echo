from launch import LaunchDescription
from launch_ros.actions import Node
import os

def generate_launch_description():
    slam_config = os.path.join(
        os.path.expanduser("~"),
        "ros2_ws/src/robot_controller/slam_config.yaml"
    )
    return LaunchDescription([
        Node(
            package="slam_toolbox",
            executable="sync_slam_toolbox_node",
            name="slam_toolbox",
            output="screen",
            parameters=[slam_config],
            remappings=[("/odom", "/odometry/filtered")]
        )
    ])
