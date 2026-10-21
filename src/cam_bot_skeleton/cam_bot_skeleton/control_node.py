import time

import rclpy
import serial
from geometry_msgs.msg import Twist
from rclpy.node import Node
from std_msgs.msg import String

from .commands import VALID_COMMANDS, motor_packet, twist_motor_packet
from .esp32_bridge import ESP32Bridge


class ControlNode(Node):

    # Sets up the ROS node, topics, parameters, and ESP32 connection
    def __init__(self):
        super().__init__("cam_bot_control")

        # Read the settings from control.yaml
        self.declare_parameter("use_hardware", False)
        self.declare_parameter("port", "/dev/rfcomm0")
        self.declare_parameter("baud_rate", 9600)
        self.declare_parameter("motor_pwm", 70)
        self.declare_parameter("command_expiry_sec", 0.35)
        self.declare_parameter("refresh_sec", 0.10)
        self.declare_parameter("linear_reference_mps", 0.5)
        self.declare_parameter("angular_reference_radps", 1.0)

        self.use_hardware = self.get_parameter("use_hardware").value
        self.motor_pwm = self.get_parameter("motor_pwm").value
        self.command_expiry_sec = self.get_parameter("command_expiry_sec").value
        self.refresh_sec = self.get_parameter("refresh_sec").value
        self.linear_reference_mps = self.get_parameter("linear_reference_mps").value
        self.angular_reference_radps = self.get_parameter("angular_reference_radps").value

        # Use a virtual serial port for testing, otherwise use the real port
        port = self.get_parameter("port").value if self.use_hardware else "loop://"
        baud = self.get_parameter("baud_rate").value if self.use_hardware else 115200

        # Publish feedback so we can see what happens after sending commands
        self.publisher = self.create_publisher(
            String, "/cam_bot/feedback", 10
        )

        # Our original subscriber for FORWARD, BACKWARD, LEFT, etc.
        self.subscription = self.create_subscription(
            String, "/cam_bot/command", self.command_callback, 10
        )

        # New subscriber for velocity commands from teleop_twist_keyboard
        self.velocity_subscription = self.create_subscription(
            Twist, "/cmd_vel", self.velocity_callback, 10
        )

        # Create the serial connection to the ESP32 (or simulator)
        self.bridge = ESP32Bridge(port, baud)

        # Keep track of the last command and any communication problems
        self.active_command = "STOP"
        self.active_packet = motor_packet("STOP")
        self.last_command_time = None
        self.fault_latched = False
        self.last_feedback = None

        # Request STOP when the node first starts
        if not self.send_motor_command("STOP") and self.use_hardware:
            self.bridge.close()
            raise RuntimeError("Unable to confirm initial STOP")

        # Check periodically if movement commands have expired
        self.timer = self.create_timer(
            self.refresh_sec, self.check_command_timeout
        )

        self.get_logger().info(
            "Hardware mode enabled" if self.use_hardware else "Simulation mode"
        )

    # Publishes feedback when there's a new message to report
    def publish_feedback(self, message):
        if message != self.last_feedback:
            self.publisher.publish(String(data=message))
            self.get_logger().info(message)
            self.last_feedback = message

    # Sends a packet through the bridge and checks whether it worked
    def send_packet(self, packet, description):
        try:
            response = self.bridge.send_command(packet)
            self.publish_feedback(f"{response}: {description} -> {packet}")
            return True

        except (TimeoutError, serial.SerialException, OSError,
                ValueError, UnicodeError) as error:

            # If something goes wrong, stop accepting movement commands
            self.fault_latched = True
            self.active_command = "STOP"
            self.active_packet = motor_packet("STOP")
            self.last_command_time = None

            self.publish_feedback(f"COMM_ERROR: {error}")

            # The ESP32 needs its own watchdog if communication is lost
            return False

    # Converts a basic movement command into a packet and sends it
    def send_motor_command(self, command):
        packet = motor_packet(command, pwm=self.motor_pwm)
        return self.send_packet(packet, command)

    # Handles messages from our original /cam_bot/command topic
    def command_callback(self, msg):
        command = msg.data.strip().upper()

        # Reject invalid movement commands and request STOP
        if command not in VALID_COMMANDS:
            self.active_command = "STOP"
            self.active_packet = motor_packet("STOP")
            self.last_command_time = None

            self.send_motor_command("STOP")
            self.publish_feedback("REJECTED: invalid movement command")
            return

        # Stop the motors if STOP was requested
        if command == "STOP":
            self.active_command = "STOP"
            self.active_packet = motor_packet("STOP")
            self.last_command_time = None

            if self.send_motor_command("STOP"):
                self.fault_latched = False
            return

        # Don't allow new movement commands after a communication error
        if self.fault_latched:
            self.publish_feedback("REJECTED: communication fault; send STOP first")
            return

        # Save the command and send it to the bridge
        self.active_command = command
        self.active_packet = motor_packet(command, pwm=self.motor_pwm)
        self.last_command_time = time.monotonic()

        self.send_packet(self.active_packet, command)

    # Handles Twist messages coming from /cmd_vel
    def velocity_callback(self, msg):

        # Get the forward/backward and turning velocities
        try:
            packet = twist_motor_packet(
                msg.linear.x,
                msg.angular.z,
                pwm=self.motor_pwm,
                linear_reference_mps=self.linear_reference_mps,
                angular_reference_radps=self.angular_reference_radps,
            )

        except (ValueError, TypeError) as error:
            # Invalid velocity values should not result in movement
            self.active_command = "STOP"
            self.active_packet = motor_packet("STOP")
            self.last_command_time = None

            self.send_motor_command("STOP")
            self.publish_feedback(f"REJECTED: invalid /cmd_vel: {error}")
            return

        # If both velocities are zero, request STOP
        if packet == motor_packet("STOP"):
            self.active_command = "STOP"
            self.active_packet = packet
            self.last_command_time = None

            if self.send_packet(packet, "STOP"):
                self.fault_latched = False
            return

        # Don't send movement commands if communication previously failed
        if self.fault_latched:
            self.publish_feedback("REJECTED: communication fault; send STOP first")
            return

        # Save the new motor packet and send it
        self.active_command = "CMD_VEL"
        self.active_packet = packet
        self.last_command_time = time.monotonic()

        self.send_packet(packet, "CMD_VEL")

    # Stops movement if we haven't received a new command recently
    def check_command_timeout(self):
        if self.last_command_time is None:
            return

        elapsed = time.monotonic() - self.last_command_time

        if elapsed >= self.command_expiry_sec:
            # Command expired, so request STOP
            self.active_command = "STOP"
            self.active_packet = motor_packet("STOP")
            self.last_command_time = None

            self.get_logger().warn(
                "Movement command expired: requesting STOP"
            )

            self.send_packet(self.active_packet, "STOP")

        elif not self.fault_latched:
            # Keep sending the current packet while the command is still recent
            self.send_packet(self.active_packet, self.active_command)

    # Request STOP and close the serial connection when the node shuts down
    def destroy_node(self):
        try:
            self.send_motor_command("STOP")
        finally:
            self.bridge.close()

        return super().destroy_node()


# Starts the ROS node and keeps it running until we shut it down
def main(args=None):
    rclpy.init(args=args)
    node = None

    try:
        node = ControlNode()
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        # Clean up the node and shut down ROS
        if node is not None:
            node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()