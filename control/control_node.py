
from py_compile import main

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

# Initialize control node
class ControlNode(Node):

    def __init__(self):
        super().__init__("cam_bot_control")

        self.subscription = self.create_subscription(
            String,
            "/cam_bot/command",
            self.command_callback,
            10
        )

        self.publisher = self.create_publisher(
            String,
            "/cam_bot/feedback", 
            10
        )

    def command_callback(self, msg):
        print(msg.data)
        valid_commands = ["FORWARD", "BACKWARD", "LEFT", "RIGHT", "STOP"]

        command = msg.data.strip().upper()
        if command in valid_commands:
            result = "ACCEPTED"
            
        else:
            result = "REJECTED"

        feedback = String()
        feedback.data = result
        self.publisher.publish(feedback)

def main():
    rclpy.init()
    node = ControlNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()






        
