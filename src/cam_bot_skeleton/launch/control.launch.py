from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    config = str(
        Path(get_package_share_directory("cam_bot_skeleton"))
        / "config"
        / "control.yaml"
    )

    return LaunchDescription([
        Node(
            package="cam_bot_skeleton",
            executable="control_node",
            name="cam_bot_control",
            output="screen",
            parameters=[config],
        )
    ])
