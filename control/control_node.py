
import rclpy
import serial

from rclpy.node import Node
from std_msgs.msg import String
from esp32_bridge import ESP32Bridge


class ControlNode(Node):

    def __init__(self):
        super().__init__("cam_bot_control")

        # Subscribe to movement commands
        self.subscription = self.create_subscription(
            String,
            "/cam_bot/command",
            self.command_callback,
            10
        )

        # Publish command feedback
        self.publisher = self.create_publisher(
            String,
            "/cam_bot/feedback",
            10
        )

        # Virtual serial connection for local testing
        # Replace with the real ESP32 port after confirming
        # hardware settings and firmware protocol.
        self.bridge = ESP32Bridge("loop://", 115200)

        self.get_logger().info("Cam-Bot control node started")

    def command_callback(self, msg):
        valid_commands = [
            "FORWARD",
            "BACKWARD",
            "LEFT",
            "RIGHT",
            "STOP"
        ]

        command = msg.data.strip().upper()

        if command not in valid_commands:
            result = "REJECTED"

        else:
            try:
                # Send command through the serial bridge
                response = self.bridge.send_command(command)

                # loop:// only echoes the transmitted command
                result = "LOOPBACK_ECHO: " + response

            except (TimeoutError, serial.SerialException, OSError) as error:
                result = "COMM_ERROR: " + str(error)

            except UnicodeError as error:
                result = "DECODE_ERROR: " + str(error)

        # Publish feedback
        feedback = String()
        feedback.data = result
        self.publisher.publish(feedback)

        self.get_logger().info(
            f"Command: {command} | Feedback: {result}"
        )


def main():
    rclpy.init()
    node = None

    try:
        node = ControlNode()
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        if node is not None:
            node.bridge.close()
            node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
