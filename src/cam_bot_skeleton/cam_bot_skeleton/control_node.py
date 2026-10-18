import time

import rclpy
import serial
from rclpy.node import Node
from std_msgs.msg import String

from .commands import VALID_COMMANDS, motor_packet
from .esp32_bridge import ESP32Bridge


class ControlNode(Node):
    def __init__(self):
        super().__init__("cam_bot_control")

        # Read settings from config/control.yaml
        self.declare_parameter("use_hardware", False)
        self.declare_parameter("port", "/dev/rfcomm0")
        self.declare_parameter("baud_rate", 9600)
        self.declare_parameter("motor_pwm", 70)
        self.declare_parameter("command_expiry_sec", 0.35)
        self.declare_parameter("refresh_sec", 0.10)

        self.use_hardware = self.get_parameter("use_hardware").value
        self.motor_pwm = self.get_parameter("motor_pwm").value
        self.command_expiry_sec = self.get_parameter("command_expiry_sec").value
        self.refresh_sec = self.get_parameter("refresh_sec").value

        port = self.get_parameter("port").value if self.use_hardware else "loop://"
        baud = self.get_parameter("baud_rate").value if self.use_hardware else 115200

        self.publisher = self.create_publisher(String, "/cam_bot/feedback", 10)
        self.subscription = self.create_subscription(
            String, "/cam_bot/command", self.command_callback, 10
        )
        self.bridge = ESP32Bridge(port, baud)

        self.active_command = "STOP"
        self.last_command_time = None
        self.fault_latched = False
        self.last_feedback = None

        # Start with a STOP packet
        if not self.send_motor_command("STOP") and self.use_hardware:
            self.bridge.close()
            raise RuntimeError("Unable to confirm initial STOP")

        self.timer = self.create_timer(self.refresh_sec, self.check_command_timeout)
        self.get_logger().info(
            "Hardware mode enabled" if self.use_hardware else "Simulation mode"
        )

    def publish_feedback(self, message):
        if message != self.last_feedback:
            self.publisher.publish(String(data=message))
            self.get_logger().info(message)
            self.last_feedback = message

    def send_motor_command(self, command):
        try:
            packet = motor_packet(command, pwm=self.motor_pwm)
            response = self.bridge.send_command(packet)
            self.publish_feedback(f"{response}: {command} -> {packet}")
            return True
        except (TimeoutError, serial.SerialException, OSError,
                ValueError, UnicodeError) as error:
            self.fault_latched = True
            self.active_command = "STOP"
            self.last_command_time = None
            self.publish_feedback(f"COMM_ERROR: {error}")
            # A lost serial link requires the controller's own stop watchdog
            return False

    def command_callback(self, msg):
        command = msg.data.strip().upper()

        if command not in VALID_COMMANDS:
            self.active_command = "STOP"
            self.last_command_time = None
            self.send_motor_command("STOP")
            self.publish_feedback("REJECTED: invalid movement command")
            return

        if command == "STOP":
            self.active_command = "STOP"
            self.last_command_time = None
            if self.send_motor_command("STOP"):
                self.fault_latched = False
            return

        if self.fault_latched:
            self.publish_feedback("REJECTED: communication fault; send STOP first")
            return

        self.active_command = command
        self.last_command_time = time.monotonic()
        self.send_motor_command(command)

    def check_command_timeout(self):
        if self.last_command_time is None:
            return

        elapsed = time.monotonic() - self.last_command_time
        if elapsed >= self.command_expiry_sec:
            self.active_command = "STOP"
            self.last_command_time = None
            self.get_logger().warn("Movement command expired: requesting STOP")
            self.send_motor_command("STOP")
        elif not self.fault_latched:
            # Refresh active commands while the input is recent
            self.send_motor_command(self.active_command)

    def destroy_node(self):
        try:
            self.send_motor_command("STOP")
        finally:
            self.bridge.close()
        return super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = ControlNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
