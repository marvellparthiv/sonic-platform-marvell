#!/usr/bin/env python

import os

try:
    from sonic_platform_pddf_base.pddf_fan import PddfFan
    from sonic_platform.psu_fru import PsuFru
    from sonic_py_common.general import getstatusoutput_noshell, getstatusoutput_noshell_pipe
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

FPGA_I2C_BUS_NUM=1
FPGA_DEV_ADDR=0x32
FPGA_FAN_FAULT_REG_BASE=0x04

fan_to_rpm_reg_offset_map={'fan1_input': 0x20, 'fan2_input': 0x22,
                           'fan3_input': 0x24, 'fan4_input': 0x26,
                           'fan5_input': 0x28, 'fan6_input': 0x2a,
                           'fan7_input': 0x2b, 'fan8_input': 0x2c}

class Fan(PddfFan):
    """PDDF Platform-Specific Fan class"""

    def __init__(self, tray_idx, fan_idx=0, pddf_data=None, pddf_plugin_data=None, is_psu_fan=False, psu_index=0):
        # idx is 0-based
        PddfFan.__init__(self, tray_idx, fan_idx, pddf_data, pddf_plugin_data, is_psu_fan, psu_index)

    # Provide the functions/variables below for which implementation is to be overwritten
    # Since psu_fan airflow direction cant be read from sysfs, it is fixed as 'F2B' or 'intake'

    def get_max_speed(self):
        """
        Retrieves the max speed

        Returns:
            An Integer, the max speed
        """
        if self.is_psu_fan:
            psu_fru = PsuFru(self.fans_psu_index)
            max_speed = int(self.plugin_data['PSU']['valmap']['PSU_FAN_MAX_SPEED'])
            for dev in self.plugin_data['PSU']['psu_support_list']:
                if dev['Manufacturer'] == psu_fru.mfr_id and dev['Name'] == psu_fru.model:
                    max_speed = int(self.plugin_data['PSU']['valmap'][dev['MaxSpd']])
                    break           
        else:
            if self.fan_index % 2 == 0:
                max_speed = int(self.plugin_data['FAN']['FAN_INLET_MAX_SPEED']) + int((int(self.plugin_data['FAN']['FAN_INLET_MAX_SPEED']) * self.get_speed_tolerance())/100)
            else:
                max_speed = int(self.plugin_data['FAN']['FAN_EXHAUST_MAX_SPEED']) + int((int(self.plugin_data['FAN']['FAN_EXHAUST_MAX_SPEED']) * self.get_speed_tolerance())/100)

        return max_speed

    def get_speed_tolerance(self):
        """
        Retrieves tolerance value from pd plugin data

        Returns:
            An integer, the tolerance percentage
        """
        return int(self.plugin_data['FAN']['FAN_MAX_SPEED_TOLERANCE'])

    def get_speed(self):
        """
        Retrieves the speed of fan as a percentage of full speed

        Returns:
            An integer, the percentage of full fan speed, in the range 0 (off)
                 to 100 (full speed)
        """
        speed_percentage = 0

        max_speed = self.get_max_speed()

        speed = int(self.get_speed_rpm())

        speed_percentage = round((speed*100)/max_speed)
        
        return min(speed_percentage, 100)

    def get_presence(self):
        """
        Retrieves the fan presence. HW does not have a dedicated presence detection capability.
        FANs RPM is a deciding criteria to detect presence.

        Returns:
            An boolean, Fan presence status
        """
        if self.is_psu_fan:
            return True
        else:
            attr = "fan{}_input".format(self.fan_index)
            reg_offset = fan_to_rpm_reg_offset_map.get(attr, 'Not Found')
            if reg_offset is None:
                return False

            rpm_speed = self.get_fan_rpm_from_fpga(attr, reg_offset)
            if int(rpm_speed) != 0:
                val="1"
            else:
                val+"0"

            vmap = self.plugin_data['FAN']['present']['i2c']['valmap']
            if val in vmap:
                status = vmap[val]
            else:
                status = False

        return status

    def get_fan_rpm_from_fpga(self, attr, reg_offset):
        """
        Retrieves fan rpm speed by fpga read

        Returns:
            An integer, speed of fan in RPM
        """

        cmdstatus, rpm_0 = getstatusoutput_noshell(['i2cget', '-f', '-y', str(FPGA_I2C_BUS_NUM), str(FPGA_DEV_ADDR), str(reg_offset)])
        if cmdstatus != 0:
            print("Error reading reg {}".format(hex(reg_offset)))
            return 0

        reg_offset = reg_offset+1
        cmdstatus, rpm_1 = getstatusoutput_noshell(['i2cget', '-f', '-y', str(FPGA_I2C_BUS_NUM), str(FPGA_DEV_ADDR), str(reg_offset)])
        if cmdstatus != 0:
            print("Error reading reg {}".format(hex(reg_offset)))
            return 0

        rpm = (int(rpm_0, 16) << 8) + int(rpm_1, 16)

        return rpm

    def get_speed_rpm(self):
        """
        Retrieves the speed of fan in RPM

        Returns:
            An integer, Speed of fan in RPM
        """
        rpm_speed = 0
        if self.is_psu_fan:
            attr = "psu_fan{}_speed_rpm".format(self.fan_index)
            device = "PSU{}".format(self.fans_psu_index)
            output = self.pddf_obj.get_attr_name_output(device, attr)
            if output is None:
                return rpm_speed

            output['status'] = output['status'].rstrip()
            if output['status'].isalpha():
                return rpm_speed
            else:
                rpm_speed = int(float(output['status']))
        else:
            attr = "fan{}_input".format(self.fan_index)
            reg_offset = fan_to_rpm_reg_offset_map.get(attr, 'Not Found')
            if reg_offset is None:
                return 0

            rpm_speed = self.get_fan_rpm_from_fpga(attr, reg_offset)

        return rpm_speed

    def get_direction(self):
        """
        Retrieves the direction of fan
        Returns:
            A string, either FAN_DIRECTION_INTAKE or FAN_DIRECTION_EXHAUST
            depending on fan direction
        """
        direction = self.FAN_DIRECTION_NOT_APPLICABLE
        if self.is_psu_fan:
            psu_fru = PsuFru(self.fans_psu_index)
            if psu_fru.mfr_id == "not available":
                return direction
            for dev in self.plugin_data['PSU']['psu_support_list']:
                if dev['Manufacturer'] == psu_fru.mfr_id and dev['Name'] == psu_fru.model:
                    dir = dev['Dir']
                    break
        else:
            if self.fan_index % 2 == 0:
                val = "0"
            else:
                val = "1"

            vmap = self.plugin_data['FAN']['direction']['i2c']['valmap']
            if val in vmap:
                dir = vmap[val]
        return dir

    def get_target_speed(self):
        """
        Retrieves the target (expected) speed of the fan
        Returns:
            An integer, the percentage of full fan speed, in the range 0 (off)
                 to 100 (full speed)
        """
        
        return self.get_speed()

    def set_speed(self, speed):
        """
        Sets the fan speed

        Args:
            speed: An integer, the percentage of full fan speed to set fan to,
                   in the range 0 (off) to 100 (full speed)

        Returns:
            A boolean, True if speed is set successfully, False if not
        """

        print("Setting Fan speed is not allowed")
        return False

