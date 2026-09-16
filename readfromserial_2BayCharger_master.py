import serial
import struct
import time
import math
from datetime import datetime
import pandas as pd
from datetime import datetime

def main():
    ser = serial.Serial('COM9', baudrate=9600, timeout=600)
    ser.reset_input_buffer()
    print("Listening on COMx for uint16 values…")
    df_name = str(datetime.now()).replace(' ', '_').replace(':', '')[:19] + '.csv'
    time_start = time.time() 

    df = pd.DataFrame(columns = [
        "fg_soc", 
        "ttf", 
        "chg_vbat", 
        "chg_ibat", 
        "chg_vmeanwell", 
        "chg_ibat_set", 
        "chg_status1", 
        "chg_fault", 
        "bms_ok", 
        "bms_fet_status", 
        "bms_batt_status_pf", 
        "bms_batt_status_ss", 
        "bms_safety_statusA", 
        "bms_safety_statusB", 
        "bms_safety_statusC", 
        "slave_ok", 
        "slave_soc", 
        "slave_ttf", 
        "slave_vbat", 
        "slave_ibat", 
        "RST_I2CB_cntr", 
        "RST_I2CA_cntr", 
        "sw_version"])
    
    try:
        while True:
            ser.reset_input_buffer()
            data = ser.read(44)
            if len(data) < 44:
                continues
            (
               master_chg_curr_lim, 
               master_chg_vbat_adc, 
               master_chg_ibat_adc, 
               master_chg_vac_adc, 
               master_fg_soc,
               master_bms_ok,
               master_bms_fet_status,
               master_chg_status1,
               slave_ok,
               slave_soc,
               slave_ttf,
               slave_ibat,
               slave_vbat,
               master_ttf,
               master_bms_batt_status,
               master_chg_fault,               
               master_RST_I2CB_cntr,
               master_RST_I2CA_cntr,
               master_safety_statusA,
               master_safety_statusB,
               master_safety_statusC,
               SW_ver_raw
            ) = struct.unpack('<22H', data)
            master_bms_batt_status_pf = master_bms_batt_status_ss = master_chg_curr_lim = master_chg_vbat_adc = master_chg_ibat_adc = master_chg_vac_adc = master_fg_soc = master_bms_ok = master_bms_fet_status = master_chg_status1 = slave_ok = slave_soc = slave_ttf = slave_ibat = slave_vbat = master_ttf = master_bms_batt_status = master_chg_fault = master_RST_I2CB_cntr = master_RST_I2CA_cntr = master_safety_statusA = master_safety_statusB = master_safety_statusC = SW_ver_raw = 1.11111111
            master_safety_statusA = master_safety_statusB = master_safety_statusC = 0xFF

            master_chg_curr_lim = master_chg_curr_lim * 0.01  
            master_chg_vbat_adc = master_chg_vbat_adc * 0.01
            master_chg_ibat_adc = master_chg_ibat_adc * 0.01
            master_chg_vac_adc = master_chg_vac_adc * 0.01    
            #master_chg_vbat_adc_raw = master_chg_vbat_adc_raw * 2E-3
            #master_chg_ibat_adc_raw = master_chg_ibat_adc_raw * 2E-3
            slave_vbat = slave_vbat * 0.01
            slave_ibat =  slave_ibat * 0.01
            SW_ver_1 = math.floor(SW_ver_raw/100)
            SW_ver_2 = SW_ver_raw -  SW_ver_1*100 
            
            master_bms_batt_status_pf = ((master_bms_batt_status & 0x8000)) >> 12
            master_bms_batt_status_ss = ((master_bms_batt_status & 0x0800)) >> 11
            
            master_power = master_chg_vbat_adc * master_chg_ibat_adc
            if master_power > 0:
                master_ttf_dbg = (100-master_fg_soc)*216/(master_power)
            else:
                master_ttf_dbg = 0
            
            slave_power = slave_vbat * slave_ibat
            if slave_power > 0:
                slave_ttf_dbg = (100-slave_soc)*216/(slave_power)
            else:
                slave_ttf_dbg = 0
            
            now = datetime.now()            
            formatted_now = now.strftime("%Y-%m-%d %H:%M:%S")
            
            time_sec = round(time.time() - time_start, 2)
            time_min = time_sec/60            
            
            print(f"************************")
            print(f"charger/master")
            print(formatted_now)    
            print(f"run_time_min: {time_min:.1f}")
            print(f"************************")
            print(f"fg_soc: {master_fg_soc:.0f}")
            print(f"ttf: {master_ttf:.0f}")
            print(f"chg_vbat: {master_chg_vbat_adc:.2f}")
            print(f"chg_ibat: {master_chg_ibat_adc:.2f}")
            print(f"------------------------")
            print(f"chg_vmeanwell: {master_chg_vac_adc:.2f}")
            print(f"chg_ibat_set: {master_chg_curr_lim:.2f}")
            print(f"chg_status1: {master_chg_status1:.0f}")
            print(f"chg_fault: {master_chg_fault:.0f}")
            print(f"bms_ok: {master_bms_ok:.0f}")
            print(f"bms_fet_status: {master_bms_fet_status:.0f}")
            print(f"bms_batt_status_pf: {master_bms_batt_status_pf:.0f}")
            print(f"bms_batt_status_ss: {master_bms_batt_status_ss:.0f}")
            print(f"bms_safety_statusA: {master_safety_statusA:08b}")
            print(f"bms_safety_statusB: {master_safety_statusB:08b}")
            print(f"bms_safety_statusC: {master_safety_statusC:08b}")
            print(f"------------------------")
            print(f"slave_ok: {slave_ok:.0f}")
            print(f"slave_soc: {slave_soc:.0f}")
            print(f"slave_ttf: {slave_ttf:.0f}")
            print(f"slave_vbat: {slave_vbat:.2f}")
            print(f"slave_ibat {slave_ibat:.2f}")
            print(f"------------------------")
            print(f"RST_I2CB_cntr: {master_RST_I2CB_cntr:.0f}")
            print(f"RST_I2CA_cntr: {master_RST_I2CA_cntr:.0f}") 
            print(f"sw_version: {SW_ver_1:02d}_{SW_ver_2:02d}\n")

            df.loc[len(df)] = [
                f"{master_fg_soc:.0f}",
                f"{master_ttf:.0f}",
                f"{master_chg_vbat_adc:.2f}",
                f"{master_chg_ibat_adc:.2f}",
                f"{master_chg_vac_adc:.2f}",
                f"{master_chg_curr_lim:.2f}",
                f"{master_chg_status1:.0f}",
                f"{master_chg_fault:.0f}",
                f"{master_bms_ok:.0f}",
                f"{master_bms_fet_status:.0f}",
                f"{master_bms_batt_status_pf:.0f}",
                f"{master_bms_batt_status_ss:.0f}",
                f"{master_safety_statusA:08b}",
                f"{master_safety_statusB:08b}",
                f"{master_safety_statusC:08b}",
                f"{slave_ok:.0f}",
                f"{slave_soc:.0f}",
                f"{slave_ttf:.0f}",
                f"{slave_vbat:.2f}",
                f"{slave_ibat:.2f}",
                f"{master_RST_I2CB_cntr:.0f}",
                f"{master_RST_I2CA_cntr:.0f}",
                f"{SW_ver_1:02d}_{SW_ver_2:02d}"
            ]
            print(df)
            df.to_csv(df_name, index=False)

         #   time.sleep(1)
    except KeyboardInterrupt:
        print("Stopped by user")
    finally:
        ser.close()

if __name__ == '__main__':
    main()
