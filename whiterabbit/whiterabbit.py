#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import socket
from dronekit import connect

from bdffont import *
from matrixbuffer import *

# Connect to the vehicle
#vehicle = connect("/dev/ttyACM0", wait_ready=True)
vehicle = connect("/dev/serial0", baud = 57600)
print("connected")

# Matrix rows and cols in pixels
MATRIX_ROWS = 16
MATRIX_COLS = 16
RPI_HOSTNAME = "raspberrypi-IEIaYs9T71"
prv_mapped_value = -1

# Set display wrapper to either terminal or neopixel based on hostname
if socket.gethostname() == RPI_HOSTNAME:
    from neopixelwrapper import *
    display_wrapper = NeopixelWrapper()
else:
    from terminalwrapper import *
    display_wrapper = TerminalWrapper()

# Initialize font and matrix buffer
font = BDFFont("fonts/5x7.bdf")
mb = MatrixBuffer(MATRIX_ROWS, MATRIX_COLS, font, display_wrapper)

def print_message(self, attr, val):
    global prv_mapped_value
    pwm_val = val.chan8_raw
    print(f"Received PWM value: {pwm_val}")
    
    mapped_value = map_pwm_to_range(pwm_val)
    if prv_mapped_value == mapped_value or pwm_val == 1499:
        return
    else:
        prv_mapped_value = mapped_value
    

    if 0 <= mapped_value <= 25:
        x = chr(mapped_value + ord('A'))
        mb.clear()
        mb.write_string(x, (0, 0, 255), mb.ALIGN_CENTER)
        mb.show()
    if mapped_value == 28:
        display_wrapper.strip.fill((0,0,0))

def map_pwm_to_range(pwm, min_pwm=794, max_pwm=2384, new_min=0, new_max=30):
    return int(((pwm - min_pwm) / (max_pwm - min_pwm)) * (new_max - new_min) + new_min)

# Add message listener
vehicle.add_message_listener("RC_CHANNELS", print_message)

# Keep the script running
while True:
    time.sleep(2)
