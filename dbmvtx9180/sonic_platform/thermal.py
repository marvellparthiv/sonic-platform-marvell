#!/usr/bin/env python


try:
    from sonic_platform_pddf_base.pddf_thermal import PddfThermal
    from sonic_py_common.general import getstatusoutput_noshell, getstatusoutput_noshell_pipe
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

FPGA_I2C_BUS_NUM=1
FPGA_DEV_ADDR=0x32

temp_sensor_reg_offset_map={'temp1_input': 0x40,
                            'temp2_input': 0x41,
                            'temp3_input': 0x42 }

temp_index_lable_map={'temp1_sensor': 'Internal Temp Sensor',
                      'temp2_sensor': 'External-A Temp Sensor',
                      'temp3_sensor': 'External-B Temp Sensor'}

class Thermal(PddfThermal):
    """PDDF Platform-Specific Thermal class"""

    def __init__(self, index, pddf_data=None, pddf_plugin_data=None, is_psu_thermal=False, psu_index=0):
        PddfThermal.__init__(self, index, pddf_data, pddf_plugin_data, is_psu_thermal, psu_index)
        self.minimum_thermal = self.get_temperature()
        self.maximum_thermal = self.get_temperature()

    def get_presence(self):
        """
        Retrieves the presence of the thermal

        Returns:
            bool: True if thermal is present, False if not
        """
        return True

    def get_model(self):
        """
        Retrieves the model number (or part number) of the Thermal

        Returns:
            string: Model/part number of Thermal
        """
        return 'NA'

    def get_serial(self):
        """
        Retrieves the serial number of the Thermal

        Returns:
            string: Serial number of Thermal
        """
        return 'NA'

    def get_status(self):
        """
        Retrieves the operational status of the thermal

        Returns:
            A boolean value, True if thermal is operating properly,
            False if not
        """
        return True


    def get_temperature_from_fpga(self, attr, reg_offset):
        """
        Retrieves temperature value by fpga read

        Returns:
            A float, temperature value in celcius
        """

        cmdstatus, temperature = getstatusoutput_noshell(['sudo', 'i2cget', '-f', '-y', str(FPGA_I2C_BUS_NUM), str(FPGA_DEV_ADDR), str(reg_offset)])
        if cmdstatus != 0:
            print("Error reading reg {}".format(hex(reg_offset)))
            return 0

        temperature_float = float(int(temperature, 16))

        return temperature_float

    def get_temperature(self):
        '''
        Read temperature value from FPGA

        Returns:
            A float value, Temperature in celcius
        '''
        if self.is_psu_thermal:
            device = "PSU{}".format(self.thermals_psu_index)
            output = self.pddf_obj.get_attr_name_output(device, "psu_temp1_input")
            if not output:
                return None

            temp1 = output['status']
            # temperature returned is in milli celcius
            return float(temp1)/1000
        else:
            attr = "temp{}_input".format(self.thermal_index)
            reg_offset = temp_sensor_reg_offset_map.get(attr, 'Not Found')
            if reg_offset is None:
                return None

            temperature = float(self.get_temperature_from_fpga(attr, reg_offset))
            if temperature == 0:
                return None

            return float(temperature)

    def get_high_threshold(self):
        '''
        Retrives higher threshold value of  temperature from FPGA

        Returns:
            A float value, Temperature in celcius
        '''
        if self.is_psu_thermal:
            return notimplementederror
        else:
            cmdstatus, temperature = getstatusoutput_noshell(['sudo', 'i2cget', '-f', '-y', str(FPGA_I2C_BUS_NUM), str(FPGA_DEV_ADDR), str(0x50)])
            if cmdstatus != 0:
                print("Error reading reg {}".format(hex(reg_offset)))
                return 0

            return int(temperature, 16)


    def get_high_critical_threshold(self):
        '''
        Retrives high critical  threshold value of  temperature from FPGA

        Returns:
            A float value, Temperature in celcius
        '''
        if self.is_psu_thermal:
            return notimplementederror
        else:
            cmdstatus, temperature = getstatusoutput_noshell(['sudo', 'i2cget', '-f', '-y', str(FPGA_I2C_BUS_NUM), str(FPGA_DEV_ADDR), str(0x50)])
            if cmdstatus != 0:
                print("Error reading reg {}".format(hex(reg_offset)))
                return 0

            return int(temperature, 16)

    def get_low_critical_threshold(self):
        """
        Retrieves the low critical threshold temperature of thermal

        Returns:
            An integer value, lower critical temperature threshold
        """
        if not self.is_psu_thermal:
            return 0
        else:
            raise NotImplementedError

    def get_low_threshold(self):
        """
        Retrieves the low threshold temperature of thermal

        Returns:
            An integer value, lower temperature threshold
        """
        if not self.is_psu_thermal:
            return 0
        else:
            raise NotImplementedError

    def get_temp_label(self):
        """
        Retrieves the temperature sensor label

        Returns:
            A string, temperature sensor label
        """
        attr = "temp{}_sensor".format(self.thermal_index)
        sensor_label = temp_sensor_reg_offset_map.get(attr, 'Not Found')
        if sensor_label is None:
           return ""
        return str(sensor_label)

    def get_minimum_recorded(self):
        """
        Retrieves the minimum recorded temperature of thermal
        Returns:
            A float number, the minimum recorded temperature of thermal in Celsius
            up to nearest thousandth of one degree Celsius, e.g. 30.125
        """
        tmp = self.get_temperature()
        if tmp < self.minimum_thermal:
            self.minimum_thermal = tmp
        return self.minimum_thermal

    def get_maximum_recorded(self):
        """
        Retrieves the maximum recorded temperature of thermal
        Returns:
            A float number, the maximum recorded temperature of thermal in Celsius
            up to nearest thousandth of one degree Celsius, e.g. 30.125
        """
        tmp = self.get_temperature()
        if tmp > self.maximum_thermal:
            self.maximum_thermal = tmp
        return self.maximum_thermal

