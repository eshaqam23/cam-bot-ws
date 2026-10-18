import serial


class ESP32Bridge:
    def __init__(self, port, baud_rate, timeout=0.2):
        # loop:// is for testing without the robot
        self.simulation = (port == "loop://")
        self.connection = serial.serial_for_url(
            port, baudrate=baud_rate, timeout=timeout, write_timeout=timeout
        )

    def send_command(self, packet):
        # Check the motor speeds and directions
        fields = packet.strip().split(",")
        if len(fields) != 4:
            raise ValueError("Expected left_pwm,left_dir,right_pwm,right_dir")
        try:
            left_pwm, left_dir, right_pwm, right_dir = map(int, fields)
        except ValueError as error:
            raise ValueError("Motor packet must contain integers") from error
        if not (0 <= left_pwm <= 255 and 0 <= right_pwm <= 255
                and left_dir in (0, 1) and right_dir in (0, 1)):
            raise ValueError("Invalid motor speed or direction")

        normalized = f"{left_pwm},{left_dir},{right_pwm},{right_dir}"

        # TODO: Confirm the controller uses this packet format and OK/ERR replies
        self.connection.reset_input_buffer()
        self.connection.write((normalized + "\n").encode("ascii"))
        self.connection.flush()

        # Read the response from the controller
        for _ in range(3):
            raw = self.connection.readline()
            if not raw:
                break
            response = raw.decode("ascii", errors="replace").strip()

            if self.simulation:
                if response == normalized:
                    return "SIM_ECHO"
            else:
                if response == "OK":
                    return "OK"
                if response == "ERR":
                    raise ValueError("Motor controller returned ERR")

        raise TimeoutError("No valid acknowledgment from motor controller")

    def close(self):
        if self.connection.is_open:
            self.connection.close()
