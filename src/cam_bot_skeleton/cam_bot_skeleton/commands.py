# Convert movement commands to left/right motor speeds
# Packet: left_pwm,left_dir,right_pwm,right_dir
VALID_COMMANDS = {"FORWARD", "BACKWARD", "LEFT", "RIGHT", "STOP"}
MAX_PWM = 90
DEFAULT_PWM = 70  # TODO: Adjust after testing motor speed at the lab


def motor_packet(command, pwm=DEFAULT_PWM):
    command = command.strip().upper()

    if command not in VALID_COMMANDS:
        raise ValueError(f"Unknown movement command: {command}")
    if type(pwm) is not int or not 0 <= pwm <= MAX_PWM:
        raise ValueError(f"PWM must be an integer from 0 to {MAX_PWM}")

    if command == "STOP":
        return "0,1,0,1"

    # TODO: Check left/right motor directions with the wheels off the ground
    # This assumes separate left and right motors, not a steering servo
    mapping = {
        "FORWARD":  (pwm, 1, pwm, 1),
        "BACKWARD": (pwm, 0, pwm, 0),
        "LEFT":     (pwm, 0, pwm, 1),
        "RIGHT":    (pwm, 1, pwm, 0),
    }
    return ",".join(str(value) for value in mapping[command])
