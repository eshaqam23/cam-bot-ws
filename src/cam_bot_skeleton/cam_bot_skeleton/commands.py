import math

# Converts movement commands into left and right motor speeds/directions
# Packet format: left_pwm,left_dir,right_pwm,right_dir

VALID_COMMANDS = {"FORWARD", "BACKWARD", "LEFT", "RIGHT", "STOP"}
MAX_PWM = 90
DEFAULT_PWM = 70  # TODO: Adjust speed after testing the actual car


# Takes a basic movement command and converts it into a motor packet
def motor_packet(command, pwm=DEFAULT_PWM):
    command = command.strip().upper()

    # Make sure the command and speed are valid
    if command not in VALID_COMMANDS:
        raise ValueError(f"Unknown movement command: {command}")

    if type(pwm) is not int or not 0 <= pwm <= MAX_PWM:
        raise ValueError(f"PWM must be an integer from 0 to {MAX_PWM}")

    # Set both motor speeds to zero if we're stopping
    if command == "STOP":
        return "0,1,0,1"

    # Each command sets the speed and direction of both motors
    # TODO: Double check motor directions during hardware testing
    mapping = {
        "FORWARD":  (pwm, 1, pwm, 1),
        "BACKWARD": (pwm, 0, pwm, 0),
        "LEFT":     (pwm, 0, pwm, 1),
        "RIGHT":    (pwm, 1, pwm, 0),
    }

    # Convert the numbers into a string that the ESP32 can read
    return ",".join(str(value) for value in mapping[command])


# Converts /cmd_vel linear and angular velocities into left/right motor values
def twist_motor_packet(linear_x, angular_z, pwm=DEFAULT_PWM,
                       linear_reference_mps=0.5, angular_reference_radps=1.0):

    # Check that the PWM and velocity values are valid
    if type(pwm) is not int or not 0 <= pwm <= MAX_PWM:
        raise ValueError(f"PWM must be an integer from 0 to {MAX_PWM}")

    if not all(math.isfinite(v) for v in
               (linear_x, angular_z, linear_reference_mps, angular_reference_radps)):
        raise ValueError("Velocity values must be finite")

    if linear_reference_mps <= 0 or angular_reference_radps <= 0:
        raise ValueError("Velocity reference values must be positive")

    # Scale the forward and turning speeds using our reference values
    forward = linear_x / linear_reference_mps
    turn = angular_z / angular_reference_radps

    # Figure out how fast each side should move
    left = forward - turn
    right = forward + turn

    # Keep the motor speeds within our allowed range
    scale = max(1.0, abs(left), abs(right))
    left /= scale
    right /= scale

    # Convert a signed speed into a PWM value and direction bit
    def motor_values(value):
        speed = int(round(abs(value) * pwm))
        direction = 1 if value >= 0 else 0
        return speed, direction

    left_pwm, left_dir = motor_values(left)
    right_pwm, right_dir = motor_values(right)

    # Put everything into the four-number format for the serial bridge
    return f"{left_pwm},{left_dir},{right_pwm},{right_dir}"