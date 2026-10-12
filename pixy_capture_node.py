import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from pixycamev3.pixy2 import Pixy2

from .pixy_frame import build_frame, serialize_frame


# Fill in the IDs configured for each trained color signature in PixyMon.
SIGNATURE_COLORS = {}


class PixyCaptureNode(Node):
    def __init__(self):
        super().__init__("pixy_capture_node")

        self.pixy_camera = Pixy2(port=1, i2c_address=0x54)
        self.publisher = self.create_publisher(String, "/pixy/detections", 10)
        self.poll_id = 0
        self.timer = self.create_timer(0.05, self._on_timer)
        self.get_logger().info(
            "Pixy detection publisher is running on /pixy/detections."
        )

    def _on_timer(self):
        capture_timestamp = time.time()
        try:
            detected_blocks = self.pixy_camera.get_blocks()
            frame = build_frame(
                self.poll_id,
                capture_timestamp,
                detected_blocks,
                SIGNATURE_COLORS,
            )
        except Exception as exc:
            frame = build_frame(
                self.poll_id,
                capture_timestamp,
                [],
                SIGNATURE_COLORS,
                status="error",
                error=str(exc),
            )
            self.get_logger().error(f"Pixy read failed: {exc}")

        message = String()
        message.data = serialize_frame(frame)
        self.publisher.publish(message)
        self.poll_id += 1


def main(args=None):
    rclpy.init(args=args)
    node = PixyCaptureNode()

    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
