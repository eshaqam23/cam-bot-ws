# cam-bot-ws

ROS 2 workspace for the VT CRO camera robot. It starts an Intel RealSense camera and turns `cmd_vel` into differential-drive commands for an ESP32 over USB serial.

The robot runtime is a Linux machine with ROS 2. The ESP32 appears as `/dev/ttyUSB0`.

## Layout

```
src/
  esp_bridge/      ROS 2 node that writes motor commands over serial
  robot_bringup/   Launch files
  motor_logic/     ESP32 Arduino sketch (built outside colcon)
```

`esp_bridge` and `robot_bringup` are ament Python packages. `motor_logic` is firmware only: it has no `package.xml`, so colcon does not build it.

## Data flow

1. A publisher sends `geometry_msgs/Twist` on `cmd_vel`. Keyboard teleop is the intended source.
2. `motor_commands` mixes `linear.x` and `angular.z` into left and right wheel speeds.
3. The node writes one line to the ESP32. The sketch drives the H-bridge and answers `OK` or `ERR`.
4. `start_rc.launch.py` starts the RealSense camera.

Wheelbase is 0.2032 m (8 in):

```
left  = linear.x - angular.z * wheelbase / 2
right = linear.x + angular.z * wheelbase / 2
```

Each wheel's absolute speed is scaled so 0.5 m/s is PWM 255, then clamped to 0–255. Direction is `1` forward and `0` backward.

## Serial protocol

9600 baud, 8N1, port `/dev/ttyUSB0`.

ROS sends one line, terminated by `\n`:

```
<left_pwm>,<left_dir>,<right_pwm>,<right_dir>
```

Example: full speed straight ahead is `255,1,255,1`.

The ESP32 prints `Ready` after boot. Each valid command gets `OK`. A line that does not parse as four integers gets `ERR`. PWM `0` stops that side.

`motor_commands` also publishes the line it sent on `ros_data` and the line it read on `esp_data` (`std_msgs/String`).

## ESP32 pins

Defined in `src/motor_logic/helpers.h`.

| Side  | Input A | Input B | PWM enable |
| ----- | ------- | ------- | ---------- |
| Left  | GPIO 0 (`IN3`) | GPIO 2 (`IN4`) | GPIO 25 (`ENB`) |
| Right | GPIO 16 (`IN1`) | GPIO 4 (`IN2`) | GPIO 26 (`ENA`) |

## Dependencies

- ROS 2 with `rclpy`, `geometry_msgs`, and `std_msgs`
- `realsense2_camera` (Intel RealSense ROS 2 wrapper)
- `teleop_twist_keyboard`, if you drive from the keyboard
- `python3-serial` (PySerial), used by `motor_commands`
- `xterm`, used when the teleop node is launched from `start_rc.launch.py`
- An ESP32 board package in the Arduino IDE (or equivalent) for `motor_logic`

The user that opens the serial port needs access to `/dev/ttyUSB0` (on Ubuntu, membership in the `dialout` group).

## Build

From the workspace root, after sourcing your ROS 2 distro:

```bash
source /opt/ros/<distro>/setup.bash
colcon build
source install/setup.bash
```

Source `install/setup.bash` in every new terminal.

Flash `src/motor_logic/motor_logic.ino` to the ESP32 with the Arduino IDE. Colcon will print a warning that `src/motor_logic` has no `package.xml`. To silence that, add an empty `COLCON_IGNORE` file in that directory.

## Run

```bash
ros2 launch robot_bringup start_rc.launch.py
```

That launch file currently starts only the RealSense camera (`realsense2_camera` `rs_launch.py`). `teleop_twist_keyboard` and `motor_commands` are present in the file and commented out.

Run the motor bridge on its own:

```bash
ros2 run esp_bridge motor_commands
```

Drive from another terminal:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

## Test

```bash
colcon test --packages-select esp_bridge robot_bringup
colcon test-result --verbose
```

The packages ship the standard ament copyright, flake8, and pep257 checks. Copyright checks are skipped until source files have a copyright header.
