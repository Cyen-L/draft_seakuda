# Import library
import datetime
import serial
import serial.tools.list_ports
import pyvisa
import time
import csv
import os
from pathlib import Path
import struct

# Define functions
def encode(cmd):
    return (cmd + '\n').encode('ascii')

def main():

    # Initial port mapping
    PWA1_port = 'COM5'
    PWA2_port = 'COM6'
    DMM1_port = 'USB0::0x1AB1::0x09C4::DM3R275204147::INSTR'
    DMM2_port = 'USB0::0x1AB1::0x09C4::DM3R275104103::INSTR'
    PSU_port = 'COM7'
    ELD_port = 'USB0::0x2EC7::0x8615::800814011817040002::INSTR'
    UPS_port = 'COM8'

    # Initial parameters
    CYCLE_LIMIT = 5
    
    # Create CSV file with timestamp
    csv_path = rf'.\test_results_{time.strftime("%Y%m%d_%H%M", time.localtime())}.csv'

    # Write header to CSV
    with open(csv_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Time',
            'Mode',
            'PWA1', 'PWA2', 'DMM1', 'DMM2', 'UPS_Vac_rms_raw',
            'UPS_Vpack_raw',
            'UPS_MB_BMS_fetsON',
            'UPS_sw_fault',
            'UPS_Iac_rms_raw',
            'UPS_Ibat_raw',
            'UPS_fet_status',
            'UPS_sw_fault_code',
            'UPS_Pac_avg_raw',
            'UPS_Vpack_BB_raw',
            'UPS_bms_ok',
            'UPS_UPS_ST_raw',
            'UPS_Vhv_serial_raw',
            'UPS_Ibat_BB_raw',
            'UPS_Vlv_raw',
            'UPS_temp_TF_raw',
            'UPS_max_cell_temp',
            'UPS_max_cell_temp_BB',
            'UPS_max_int_temp',
            'UPS_max_int_temp_BB',
            'UPS_max_cell_volt_raw',
            'UPS_max_cell_volt_BB_raw',
            'UPS_min_cell_volt_raw',
            'UPS_min_cell_volt_BB_raw',
            'UPS_soc',
            'UPS_perm_fault',
            'UPS_BB_perm_fault',
            'UPS_I2CB_freeze_cntr',
            'UPS_I2CA_freeze_cntr',
            'UPS_p_usb',
            'UPS_SW_ver_raw'
        ])

    # Create connections
    rm = pyvisa.ResourceManager()
    PWA1 = serial.Serial(port=PWA1_port, baudrate=9600, timeout=0.2)
    PWA2 = serial.Serial(port=PWA2_port, baudrate=9600, timeout=0.2)
    DMM1 = rm.open_resource(DMM1_port)
    DMM2 = rm.open_resource(DMM2_port)
    PSU = serial.Serial(port=PSU_port, baudrate=9600, timeout=0.2)
    ELD = rm.open_resource(ELD_port)
    UPS = serial.Serial(port=UPS_port, baudrate=9600, timeout=3)

    try:
        # Initial configuration
        PSU.write(encode('*RST')) # Reset PSU to default state
        ELD.write('*RST') # Reset ELD to default state
        PWA1.write(encode('*RST')) # Reset PWA1 to default state
        PWA2.write(encode('*RST')) # Reset PWA2 to default state
        DMM1.write('*RST') # Reset DMM1 to default state
        DMM2.write('*RST') # Reset DMM2 to default state
        time.sleep(2)
        PSU.write(encode('VOLT:RANGE R310')) # Set voltage range to 310V for better resolution
        PSU.write(encode('VOLT 120')) # Set voltage to 120V for discharge mode
        PSU.write(encode('FREQ 60')) # Set frequency to 60Hz for discharge mode
        PSU.write(encode('CURR:LIM:RMS 4.2')) # Set current limit to 4.2A for charge mode
        ELD.write('SYST:MODE AC') # Set ELD to AC mode for both charge and discharge
        ELD.write('FUNC POWER') # Set ELD to control power for both charge and discharge
        ELD.write('POWER 250') # Set ELD to 250W for discharge mode
        PWA1.write(encode('INP:MODE AC')) # Set PWA1 to AC mode for discharge measurements
        PWA2.write(encode('INP:MODE AC')) # Set PWA2 to AC mode for discharge measurements
        DMM1.write('FUNC "VOLT:DC"') # Set DMM1 to measure DC voltage
        DMM2.write('FUNC "VOLT:DC"') # Set DMM2 to measure DC voltage
        #DMM1.write('MEASure:VOLTage:DC:RANGE 0') # For Rigol DMMs
        #DMM2.write('MEASure:VOLTage:DC:RANGE 0') # For Rigol DMMs
        time.sleep(2)

        # Initialize mode and UPS reading
        mode = 'discharge'
        cycle_count = 0

        # Initalize battery life reading
        temp = b''
        n = 0

        # Handling UPS reading
        # Loop until we get a valid reading with correct length and end byte
        while len(temp) < 62:

            # Reset input buffer before reading to avoid stale data
            UPS.reset_input_buffer()

            # Read data from UPS
            temp = UPS.read(62)

            # If the length is incorrect, discard and try again
            if len(temp) < 62:
                continue

            # Unpack the data
            resp = struct.unpack('<31h', temp)

            # Check if the last byte is the expected end byte (145)
            # 145 is the SW version byte (UPS_SW_ver_raw), which always should be 145 for our UPS until the firmware is updated
            # And it is used as a simple validation check to ensure we have a correct position in the data stream
            if resp[-1] != 145:

                # Reset temp to force another read if the end byte is not correct
                temp = b''

            # Check loop count to avoid infinite loop in case of persistent read issues
            if n > 20:
                print("Failed to get valid UPS reading after 20 attempts, please check the UPS connection.")
            n += 1
        
        # Retrive battery life (SOC) from the unpacked data
        battery_life = struct.unpack('<31h', temp)[-7]
        
        # Start test
        ELD.write('INP ON')
        PSU.write(encode('OUTP OFF'))

        # Start looping
        while True:

            # Check if we have completed 5 full discharge cycles (from 100% to 15% SOC)
            if cycle_count >= CYCLE_LIMIT:
                print("Completed 5 discharge cycles, stopping.")
                break

            # Switch to discharge mode if battery life is above 100%
            if battery_life >= 100 and mode != 'discharge':
                PSU.write(encode('OUTP OFF'))
                ELD.write('POWER 250')
                mode = 'discharge'
                cycle_count += 1

            # Switch to charge mode if battery life is below 15%
            if battery_life <= 15 and mode != 'charge':
                PSU.write(encode('OUTP ON'))
                ELD.write('POWER 150')
                mode = 'charge'

            # Initalize output variables
            temp = b''

            # Handling UPS reading
            # Loop until we get a valid reading with correct length and end byte
            while len(temp) < 62:
                
                # Reset input buffer before reading to avoid stale data
                # Disable since continously resetting the buffer may cause misalignment issues and prevent us from getting a valid reading
                #UPS.reset_input_buffer()

                # Read data from UPS
                temp = UPS.read(62)

                # Unpack the data
                resp = struct.unpack('<31h', temp)

                # Check if the last byte is the expected end byte (145)
                # 145 is the SW version byte (UPS_SW_ver_raw), which always should be 145 for our UPS until the firmware is updated
                # And it is used as a simple validation check to ensure we have a correct position in the data stream
                if resp[-1] != 145:

                    # Reset the output
                    temp = b''

                    # Reset input buffer to clear any stale or misaligned data before the next read attempt
                    UPS.reset_input_buffer()

                    # To avoid infinite loop in case of persistent read issues that might caused overcharging or overdischarging
                    if resp[-7] >= 99 or resp[-7] <= 15:
                        break

            # Unpack the data into individual variables for better readability
            (
                UPS_Vac_rms_raw,
                UPS_Vpack_raw,
                UPS_MB_BMS_fetsON,
                UPS_sw_fault,
                UPS_Iac_rms_raw,
                UPS_Ibat_raw,
                UPS_fet_status,
                UPS_sw_fault_code,
                UPS_Pac_avg_raw,
                UPS_Vpack_BB_raw,
                UPS_bms_ok,
                UPS_UPS_ST_raw,
                UPS_Vhv_serial_raw,
                UPS_Ibat_BB_raw,
                UPS_Vlv_raw,
                UPS_temp_TF_raw,
                UPS_max_cell_temp,
                UPS_max_cell_temp_BB,
                UPS_max_int_temp,
                UPS_max_int_temp_BB,
                UPS_max_cell_volt_raw,
                UPS_max_cell_volt_BB_raw,
                UPS_min_cell_volt_raw,
                UPS_min_cell_volt_BB_raw,
                UPS_soc,
                UPS_perm_fault,
                UPS_BB_perm_fault,
                UPS_I2CB_freeze_cntr,
                UPS_I2CA_freeze_cntr,
                UPS_p_usb,
                UPS_SW_ver_raw
            ) = resp

            # Get the current timestamp and battery life for logging
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            battery_life = UPS_soc

            # Read measurements
            PWA1.write(encode('NUM:NORM:VALUE?'))
            PWA2.write(encode('NUM:NORM:VALUE?'))
            DMM1.write('MEASure:VOLTage:DC?')
            DMM2.write('MEASure:VOLTage:DC?')
            PWA1_resp = PWA1.readline().decode().strip()
            PWA2_resp = PWA2.readline().decode().strip()
            DMM1_resp = DMM1.read().strip()
            DMM2_resp = DMM2.read().strip()

            # Write results to CSV
            with open(csv_path, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([
                    timestamp, mode,
                    PWA1_resp, PWA2_resp, DMM1_resp, DMM2_resp,
                    UPS_Vac_rms_raw, UPS_Vpack_raw, UPS_MB_BMS_fetsON,
                    UPS_sw_fault, UPS_Iac_rms_raw, UPS_Ibat_raw,
                    UPS_fet_status, UPS_sw_fault_code, UPS_Pac_avg_raw,
                    UPS_Vpack_BB_raw, UPS_bms_ok, UPS_UPS_ST_raw,
                    UPS_Vhv_serial_raw, UPS_Ibat_BB_raw, UPS_Vlv_raw,
                    UPS_temp_TF_raw, UPS_max_cell_temp, UPS_max_cell_temp_BB,
                    UPS_max_int_temp, UPS_max_int_temp_BB,
                    UPS_max_cell_volt_raw, UPS_max_cell_volt_BB_raw,
                    UPS_min_cell_volt_raw, UPS_min_cell_volt_BB_raw,
                    UPS_soc, UPS_perm_fault, UPS_BB_perm_fault,
                    UPS_I2CB_freeze_cntr, UPS_I2CA_freeze_cntr,
                    UPS_p_usb, UPS_SW_ver_raw
                ])
            print(f"End Timestamp: {timestamp}, Mode: {mode}, Cycle: {cycle_count}, SOC: {battery_life}, Temp: {UPS_temp_TF_raw}")

    # Handle user interruption and ensure resources are closed properly
    except KeyboardInterrupt:
        print("Stopped by user")
    
    # Finally block to ensure resources are closed even if an error occurs
    finally:
        try:
            PSU.write(encode('OUTP OFF'))
            ELD.write('INP OFF')
        except Exception as e:
            print(e)
        
        PWA1.close()
        PWA2.close()
        PSU.close()
        UPS.close()
        DMM1.close()
        DMM2.close()
        ELD.close()
        rm.close()
        print("Resources closed.")

if __name__ == "__main__":
    main()