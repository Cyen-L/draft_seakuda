import serial
import pyvisa
import serial.tools.list_ports


def get_port_info(port, baudrate=9600, timeout=0.2):
	'''Get device information from a specified COM port by sending SCPI commands'''

	# Initialize default values for model and serial number in case we cannot retrieve them from the port
	model = "Unknown Device"
	serial_number = "Unknown Device"
	manufacturer = "Unknown Manufacturer"

	serial_port = None
	inst = None

	# Check if the port is a COM port before attempting to open it and send commands
	# If it is a COM port, we will open it using pyserial
	if port[:3] == 'COM':
		try:
			
			# Initialize serial_port variable to None before the try block so that we can reference it in the except block if an error occurs during initialization
			serial_port = None

			# Initialize a serial connection to the specified port with the given baud rate and timeout settings.
			serial_port = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)

			# Get model information
			serial_port.write("*IDN?\n".encode("utf-8"))
			response = serial_port.read(256).decode("utf-8").split(',')
			if response and response != ['']:
				manufacturer = response[0]
				model = response[1]
				serial_number = response[2]

			# Close the serial connection after retrieving the information
			serial_port.close()

		except serial.SerialException as e:

			# Log the error that occurred while trying to get port information
			print(f"Error while retrieving port information from {port}: {e}")

		# Ensure that the serial port is closed if it was opened before the error occurred to prevent resource leaks
		finally:
			if serial_port and serial_port.is_open:
				serial_port.close()

	elif port[:3] == 'USB':
		try:

			# Initialize a VISA resource manager
			rm = pyvisa.ResourceManager()

			# Open the VISA resource corresponding to the specified port
			inst = rm.open_resource(port)

			# Open the VISA resource corresponding to the specified port
			response = [item.strip() for item in inst.query('*IDN?').split(',')]

			# Get model and serial number information from the VISA resource response
			manufacturer = response[0]
			model = response[1]
			serial_number = response[2]

			# Close the VISA resource after retrieving the information
			inst.clear()
			
		except pyvisa.Error as e:

			# Log the error that occurred while trying to get port information
			print(f"Error while retrieving port information from {port}: {e}")
		
		# Ensure that the VISA resource is closed if it was opened before the error occurred to prevent resource leaks
		finally:
			if inst:
				inst.clear()
				inst.close()

	else:
		model = "Unknown Device"
		serial_number = "Unknown Device"
		manufacturer = "Unknown Manufacturer"

	return {"port": port, 'manufacturer': manufacturer, 'model': model, "serial_number": serial_number}

def main():
	# Get the list of available serial ports and VISA resources using pyserial and pyvisa
  serial_ports = [p.device for p in list(serial.tools.list_ports.comports())]
  visa_ports = list(pyvisa.ResourceManager().list_resources())


  # Retrieve device information
  serial_ports_info = [get_port_info(p) for p in serial_ports]
  visa_ports_info = [get_port_info(p) for p in visa_ports]
  all_ports_info = serial_ports_info + visa_ports_info

  for device in all_ports_info:
    print(f"{device['port']} - {device['manufacturer']} {device['model']} - {device['serial_number']}")
if __name__ == "__main__":
    main()