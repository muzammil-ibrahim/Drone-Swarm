# Requirements

### Hardware
- Raspberry Pi
- Neopixel strips (144 leds/m recommended). Get it from either [Adafruit](https://www.adafruit.com/product/1506) or much cheaper options at AliExpress (search for "ws2812b led strips")

### Software
- Any Linux based OS running on Raspberry Pi
- Python
- [rpi_ws281x library](https://github.com/jgarff/rpi_ws281x). Tutorial on using: https://learn.adafruit.com/neopixels-on-raspberry-pi/overview

```
# TL;DR for installing rpi_ws281x library

# install pip if not installed
$ sudo apt install python3-pip

# install libraries
$ sudo pip3 install rpi_ws281x adafruit-circuitpython-neopixel
$ sudo pip3 install dronekit
```

## Running

Before running, there are few modifications to the code you might have to do:

- in `neopixelwrapper.py`:
  - modify the `LED_COUNT`, `LED_PIN`, and `LED_ORDER` variables
  - modify `matrix_to_array` function to match the layout of the neopixel matrix
- in `whiterabbit.py`:
  - modify `MATRIX_ROWS`, `MATRIX_COLS` to match rows and columns of pixel in the matrix
  - modify `RPI_HOSTNAME` to match the hostname the code is running on. otherwise it'll emulate the matrix on terminal
  - modify the vehicle's connection string  

Once everything is set,navigate to the directory and run:

```
sudo python3 whiterabbit.py
``` 

However, before doing that, read how to build the matrix, connect it to Raspberry Pi, and adjust the settings below.

### Neomatrix layout

The leds are arranged this "serpentine" way:

```
  x - x - x - x - x - x - x --- to raspberry pi
  |
  |
  x - x - x - x - x - x - x 
                          |
                          |
  x - x - x - x - x - x - x 
  |
  |
  x - x - x - x - x - x - x 
                          |
                          |
  x - x - x - x - x - x - x 
```

If five strips of neopixels with 144 pixels/m are arranged in this way, the pixel numberings will be as follows:

```
 143 - x - x - x - x - x -- 0 --- to raspberry pi
  |
  |
 144 - x - x - x - x - x - 287
                            |
                            |
 431 - x - x - x - x - x - 288
  |	
  |
 432 - x - x - x - x - x - 575
                            |
                            |
 719 - x - x - x - x - x - 576

```

### Connecting to Raspberry Pi

The 5V and GND pins from the strip can be connected to any 5V and GND pin of Raspberry Pi. If there are lots of pixels and you are planning to use the full brightness, you need to connect it to external power source with higher amp.

The data pin is connected to any GPIO pin with PWM (18 by default).

See https://learn.adafruit.com/adafruit-neopixel-uberguide for more details about connection and best practices.

### Displaying text

[BDF font](https://en.wikipedia.org/wiki/Glyph_Bitmap_Distribution_Format) files are used to read data for each character. Modify the values in `whiterabbit.py` to specify the font file. The `MatrixBuffer` class is used to construct the buffer before sending the data to the neopixel strip. The `NeopixelWrapper::matrix_to_array()` converts the matrix to serial data. If the strips are arranged in a different way than described above, this function has to be adjusted to change the mapping.

`MatrixBuffer` has helper functions to display character text or character.





