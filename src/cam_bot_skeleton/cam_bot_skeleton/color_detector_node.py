"""Basic color-based computer vision for Cam-Bot camera images."""

import json

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge, CvBridgeError
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String


class ColorDetectorNode(Node):
    """Subscribe to camera images and publish detected colored regions as JSON."""

    def __init__(self):
        super().__init__("color_detector")

        self.declare_parameter("image_topic", "/camera/image_raw")
        self.declare_parameter("observations_topic", "/cam_bot/observations")
        self.declare_parameter("min_area", 500.0)
        self.declare_parameter("blur_kernel", 5)
        # OpenCV HSV hue is 0..179; saturation/value are 0..255.
        self.declare_parameter("red_lower_1", [0, 100, 70])
        self.declare_parameter("red_upper_1", [10, 255, 255])
        self.declare_parameter("red_lower_2", [170, 100, 70])
        self.declare_parameter("red_upper_2", [179, 255, 255])
        self.declare_parameter("green_lower", [35, 70, 50])
        self.declare_parameter("green_upper", [85, 255, 255])
        self.declare_parameter("blue_lower", [90, 70, 50])
        self.declare_parameter("blue_upper", [135, 255, 255])

        self.bridge = CvBridge()
        self.min_area = float(self.get_parameter("min_area").value)
        self.blur_kernel = max(1, int(self.get_parameter("blur_kernel").value))
        if self.blur_kernel % 2 == 0:
            self.blur_kernel += 1

        image_topic = self.get_parameter("image_topic").value
        observations_topic = self.get_parameter("observations_topic").value
        self.publisher = self.create_publisher(String, observations_topic, 10)
        self.subscription = self.create_subscription(
            Image, image_topic, self._on_image, 10
        )
        self.frame_count = 0
        self.get_logger().info(
            f"Color detector listening on {image_topic}; "
            f"publishing JSON observations on {observations_topic}"
        )

    def _range(self, parameter_name):
        return np.array(self.get_parameter(parameter_name).value, dtype=np.uint8)

    def _mask_for_color(self, hsv, color):
        if color == "red":
            mask1 = cv2.inRange(
                hsv, self._range("red_lower_1"), self._range("red_upper_1")
            )
            mask2 = cv2.inRange(
                hsv, self._range("red_lower_2"), self._range("red_upper_2")
            )
            return cv2.bitwise_or(mask1, mask2)
        return cv2.inRange(
            hsv,
            self._range(f"{color}_lower"),
            self._range(f"{color}_upper"),
        )

    def _on_image(self, msg):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        except CvBridgeError as exc:
            self.get_logger().warning(f"Could not convert camera image: {exc}")
            return

        height, width = frame.shape[:2]
        kernel = self.blur_kernel
        if kernel > 1:
            frame = cv2.GaussianBlur(frame, (kernel, kernel), 0)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        detections = []
        for color in ("red", "green", "blue"):
            mask = self._mask_for_color(hsv, color)
            mask = cv2.morphologyEx(
                mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)
            )
            mask = cv2.morphologyEx(
                mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)
            )
            contours, _ = cv2.findContours(
                mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            for contour in contours:
                area = float(cv2.contourArea(contour))
                if area < self.min_area:
                    continue
                x, y, box_width, box_height = cv2.boundingRect(contour)
                moments = cv2.moments(contour)
                if moments["m00"] == 0:
                    continue
                cx = int(moments["m10"] / moments["m00"])
                cy = int(moments["m01"] / moments["m00"])
                detections.append({
                    "color": color,
                    "center_px": {"x": cx, "y": cy},
                    "center_normalized": {
                        "x": round(cx / max(width - 1, 1), 4),
                        "y": round(cy / max(height - 1, 1), 4),
                    },
                    "bbox_xywh": [int(x), int(y), int(box_width), int(box_height)],
                    "area_px": round(area, 1),
                })

        self.frame_count += 1
        observation = {
            "frame_id": self.frame_count,
            "stamp": {
                "sec": int(msg.header.stamp.sec),
                "nanosec": int(msg.header.stamp.nanosec),
            },
            "image_width": int(width),
            "image_height": int(height),
            "detections": detections,
        }
        output = String()
        output.data = json.dumps(observation)
        self.publisher.publish(output)


def main(args=None):
    rclpy.init(args=args)
    node = ColorDetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
