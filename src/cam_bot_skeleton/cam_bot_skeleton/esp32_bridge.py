import serial


class ESP32Bridge:

    # Opens the serial connection using the port and baud rate we provide
    def __init__(self, port, baud_rate, timeout=0.2):

        # loop:// lets us test without the actual ESP32
        self.simulation = (port == "loop://")

        self.connection = serial.serial_for_url(
            port,
            baudrate=baud_rate,
            timeout=timeout,
            write_timeout=timeout
        )

    # Checks the packet, sends it to the ESP32, and waits for a response
    def send_command(self, packet):

        # Split the packet into the four motor values
        fields = packet.strip().split(",")

        if len(fields) != 4:
            raise ValueError("Expected left_pwm,left_dir,right_pwm,right_dir")

        try:
            left_pwm, left_dir, right_pwm, right_dir = map(int, fields)

        except ValueError as error:
            raise ValueError("Motor packet must contain integers") from error

        # Make sure the speed and direction values make sense
        if not (0 <= left_pwm <= 255 and 0 <= right_pwm <= 255
                and left_dir in (0, 1) and right_dir in (0, 1)):
            raise ValueError("Invalid motor speed or direction")

        # Put the packet back into the correct format
        normalized = f"{left_pwm},{left_dir},{right_pwm},{right_dir}"

        # TODO: Confirm this format and the OK/ERR responses match the ESP32 firmware

        # Clear old incoming data before sending a new command
        self.connection.reset_input_buffer()

        # Send the command as bytes, with a newline at the end
        self.connection.write((normalized + "\n").encode("ascii"))
        self.connection.flush()

        # Read up to three lines while looking for a valid response
        for _ in range(3):
            raw = self.connection.readline()

            if not raw:
                break

            response = raw.decode("ascii", errors="replace").strip()

            # In simulation, the serial port just echoes the packet back
            if self.simulation:
                if response == normalized:
                    return "SIM_ECHO"

            else:
                # Check if the actual ESP32 accepted the command
                if response == "OK":
                    return "OK"

                if response == "ERR":
                    raise ValueError("Motor controller returned ERR")

        # No valid response came back
        raise TimeoutError("No valid acknowledgment from motor controller")

    # Closes the serial connection when we're finished using it
    def close(self):
        if self.connection.is_open:
            self.connection.close()