#############################################################################
#
# Component contains an implementation of SONiC Platform Base API and
# provides the components firmware management function
#
#############################################################################

try:
    import subprocess
    from sonic_platform_base.component_base import ComponentBase
    from sonic_py_common.general import getstatusoutput_noshell, getstatusoutput_noshell_pipe
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

FPGA_I2C_BUS_NUM=1
FPGA_DEV_ADDR=0x32
FPGA_FW_VERSION_REG_OFFSET=0x00

BIOS_VERSION_PATH = "/sys/class/dmi/id/bios_version"
COMPONENT_LIST= [
   ("BIOS", "Basic Input/Output System"),
   ("SysFPGA", "System FPGA"),
]

class Component(ComponentBase):
    """Platform-specific Component class"""

    DEVICE_TYPE = "component"

    def __init__(self, component_index=0):
        self.index = component_index
        self.name = self.get_name()

    def _run_command(self, command):
        # Run bash command and print output to stdout
        try:
            process = subprocess.Popen(
                shlex.split(command), stdout=subprocess.PIPE)
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
            rc = process.poll()
            if rc != 0:
                return False
        except Exception:
            return False
        return True

    def _get_bios_version(self):
        # Retrieves the BIOS firmware version
        try:
            with open(BIOS_VERSION_PATH, 'r') as fd:
                bios_version = fd.read()
                return bios_version.strip()
        except Exception as e:
            return None

    def _get_fpga_version(self):
        # Retrieves the CPLD firmware version
        fpga_version = dict()
        cmdstatus, fpga_fw_version = getstatusoutput_noshell(['i2cget', '-f', '-y', str(FPGA_I2C_BUS_NUM), str(FPGA_DEV_ADDR), str(FPGA_FW_VERSION_REG_OFFSET)])
        if cmdstatus != 0:
            print("Error reading reg {}".format(hex(reg_offset)))
            fpga_version["SysFPGA"] = 'N/A'
        else:
            fpga_version["SysFPGA"] = str(fpga_fw_version)

        return fpga_version

    def get_name(self):
        """
        Retrieves the name of the component
         Returns:
            A string containing the name of the component
        """
        return COMPONENT_LIST[self.index][0]

    def get_description(self):
        """
        Retrieves the description of the component
            Returns:
            A string containing the description of the component
        """
        return COMPONENT_LIST[self.index][1]

    def get_firmware_version(self):
        """
        Retrieves the firmware version of module
        Returns:
            string: The firmware versions of the module
        """
        fw_version = None

        if self.name == "BIOS":
            fw_version = self._get_bios_version()
        elif "SysFPGA" in self.name:
            fpga_version = self._get_fpga_version()
            fw_version = fpga_version.get(self.name)
        return fw_version

    def install_firmware(self, image_path):
        """
        Install firmware to module
        Args:
            image_path: A string, path to firmware image
        Returns:
            A boolean, True if install successfully, False if not
        """
        raise NotImplementedError
