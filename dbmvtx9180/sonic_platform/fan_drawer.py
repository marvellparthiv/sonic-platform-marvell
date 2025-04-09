#!/usr/bin/env python


try:
    from sonic_platform_pddf_base.pddf_fan_drawer import PddfFanDrawer
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")


class FanDrawer(PddfFanDrawer):
    """PDDF Platform-Specific Fan-Drawer class"""

    def __init__(self, tray_idx, pddf_data=None, pddf_plugin_data=None):
        # idx is 0-based 
        PddfFanDrawer.__init__(self, tray_idx, pddf_data, pddf_plugin_data)

    # Provide the functions/variables below for which implementation is to be overwritten

    def get_model(self):
        """
        Retrieves the model number (or part number) of the Fan Drawer

        Returns:
            string: Model/part number of Fan Drawer
        """
        return 'NA'
    def get_serial(self):
        """
        Retrieves the serial number (or part number) of the Fan Drawer

        Returns:
            string: Serial number of Fan Drawer
        """
        return 'NA'
