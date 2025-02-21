#!/bin/bash
modprobe -r gpio_kempld
modprobe -r kempld-wdt
modprobe -r i2c_kempld
modprobe -r kempld_core

