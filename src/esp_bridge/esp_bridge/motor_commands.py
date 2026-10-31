import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String
import serial
# import math
# import numpy as np

class Motor_Commands(Node):
    """ROS2 node for communicating motor commands via USB"""
    
    def __init__(self):
        super().__init__('motor_commands')
        
        # cmd_vel subscriber        
        self.cmd_vel_sub = self.create_subscription(
            Twist,
            'cmd_vel',
            self.cmd_vel_callback,
            10
        )

        self.module_pub = self.create_publisher(String, 'esp_data', 10)
        self.ros_pub = self.create_publisher(String, 'ros_data', 10)

        # USB connection
        self.ser = serial.Serial("/dev/ttyUSB0", 9600, timeout=1)
    
    def cmd_vel_callback(self, msg):
        linear_velocity = msg.linear.x
        angular_velocity = msg.angular.z
        wheel_base = 0.2032 # 8 inches

        # calculate velocity per wheel
        left_velocity = linear_velocity - (angular_velocity * wheel_base) / 2
        right_velocity = linear_velocity  + (angular_velocity * wheel_base) / 2

        # determine wheel speed
        left_speed = abs(left_velocity)
        right_speed = abs(right_velocity)

        # determine wheel direction
        left_forward = 0 if left_velocity < 0 else 1
        right_forward = 0 if right_velocity < 0 else 1

        # normalize wheel velocity between 0 and 255
        # max(left_speed) = 0.5, max(right_speed) = 0.5
        left_speed_normalized = min(int(left_speed / 0.5 * 255), 255)
        right_speed_normalized = min(int(right_speed / 0.5 * 255), 255)

        message = f"{left_speed_normalized},{left_forward},{right_speed_normalized},{right_forward}\n"
        self.ser.write(message.encode('utf-8'))

        # Message sent by ROS
        ros_msg = String()
        ros_msg.data = message
        self.ros_pub.publish(ros_msg)

        # Message received from ESP
        if self.ser.in_waiting > 0:
            line = self.ser.readline().decode('utf-8').rstrip()
            module_msg = String()
            module_msg.data = line
            self.module_pub.publish(module_msg)
            self.get_logger().info(f'Publishing: {line}')
           

def main(args=None):
    rclpy.init(args=args)
    node = Motor_Commands()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Shutting down Motor Commands node')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()