import rclpy
from rclpy.node import Node


class SkeletonNode(Node):
    def __init__(self):
        super().__init__("skeleton_node")
        self.declare_parameter("message", "Cam bot skeleton node is running.")
        self.timer = self.create_timer(1.0, self._on_timer)

    def _on_timer(self):
        message = self.get_parameter("message").value
        self.get_logger().info(message)


def main(args=None):
    rclpy.init(args=args)
    node = SkeletonNode()

    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
