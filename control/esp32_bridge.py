
import serial


# Handles serial communication with the ESP32
class ESP32Bridge:

    def __init__(self, port, baud_rate):
        self.connection = serial.serial_for_url(
            port,
            baudrate=baud_rate,
            timeout=1
        )

    # Sends a command and returns the serial response
    def send_command(self, command):
        message = command + "\n"
        encoded_message = message.encode("utf-8")

        self.connection.write(encoded_message)

        response = self.connection.readline()

        if not response:
            raise TimeoutError("No response received from ESP32.")

        decoded_response = response.decode("utf-8").strip()
        return decoded_response

    # Closes the connection
    def close(self):
        self.connection.close()
