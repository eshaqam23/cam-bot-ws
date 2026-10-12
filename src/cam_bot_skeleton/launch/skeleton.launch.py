import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    config_file = os.path.join(
        get_package_share_directory("cam_bot_skeleton"),
        "config",
        "params.yaml",
    )

    return LaunchDescription(
        [
            Node(
                package="cam_bot_skeleton",
                executable="skeleton_node",
                name="skeleton_node",
                output="screen",
                parameters=[config_file],
            ),
        ]
    )
