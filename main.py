import os
import sys
import cherrypy
import cherrypy_cors
import time
from decimal import Decimal
from pymavlink import mavutil
from dronekit import connect, VehicleMode, LocationGlobalRelative

requires = [
    'cherrypy_cors',
]

class Root:
    global flag
    flag = False

    def __init__(self, vehicle):
        self.vehicle = vehicle

    @cherrypy.expose
    def index(self):
        return 'Hi! Welcome to Dronekit server'

    @cherrypy.expose
    def play_tune(self):
        try:
            tune_bytes = "AAA".encode("ascii")
            self.vehicle.play_tune(tune_bytes)
        except AttributeError:
            print("Unable to play the tune")
            print("vehicle connected")
        return 'Play tune'

    @cherrypy.expose
    def arm_and_takeoff(self, aTargetAltitude=None):
        global flag

        if flag:
            return f"takeoff failed"

        print("\n\nBasic pre-arm checks")
        while not self.vehicle.is_armable:
            print("\n Waiting for vehicle to initialise...")
            time.sleep(1)

        print("\nArming motors")
        self.vehicle.mode = VehicleMode("GUIDED")
        self.vehicle.armed = True

        while not self.vehicle.armed:
            print("\n Waiting for arming...")
            time.sleep(1)

        alt = int(aTargetAltitude)

        print("Taking off!")
        self.vehicle.simple_takeoff(alt)

        while True:
            print(" Altitude: ", self.vehicle.location.global_relative_frame.alt)
            if self.vehicle.location.global_relative_frame.alt >= alt * 0.95:
                print("Reached target altitude")
                break
            time.sleep(1)
        flag = True

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def state(self):
        state = {
            "system_id": self.vehicle.parameters["SYSID_THISMAV"],
            "battery": self.vehicle.battery.level,
            "gps": self.vehicle.gps_0.fix_type,
            "mode": self.vehicle.mode.name,
            "is_armable": self.vehicle.is_armable,
            "armed": self.vehicle.armed,
            "altitude": self.vehicle.location.global_relative_frame.alt,
            "location": {
                "lat": self.vehicle.location.global_relative_frame.lat,
                "lon": self.vehicle.location.global_relative_frame.lon
            }
        }
        return state

    @cherrypy.expose
    def led_fill(self):
        self.vehicle.channels.overrides = {'8': 794 + (27 * 53) + 25}
        return 'led fill'

    @cherrypy.expose
    def clear_led(self):
        self.vehicle.channels.overrides = {'8': 794 + (28 * 53) + 25}
        return 'led clear'

    @cherrypy.expose
    def display_letter(self, ch=None):
        ch = ch or 'a'
        switch = {char: idx for idx, char in enumerate('abcdefghijklmnopqrstuvwxyz?')}
        k = switch.get(ch, -1)
        x = str(k)
        self.vehicle.channels.overrides = {'8': (800 + (k * 53)) + 20}
        return f"Received ch: {x}"
    
    def goto(self, lat, lon):
        print(f"Moving towards the position...,{lat}, {lon}")
        lat = Decimal(lat)
        lon = Decimal(lon)
        current_location = self.vehicle.location.global_relative_frame
        current_altitude = current_location.alt
        target_location = LocationGlobalRelative(lat, lon, current_altitude)
        print("running simple goto function.")
        self.vehicle.simple_goto(target_location)
        print("moving towards the target location for 30 seconds")
        time.sleep(30)
        print("Reached location")

    @cherrypy.expose
    def goto_pos(self, lat, lon):
        self.goto(lat, lon)
        return f"message:goto done!"
    
    @cherrypy.expose
    def change_altitude(self, changealtitude):
        inc = False
        curr = self.vehicle.location.global_relative_frame.alt
        changealtitude = float(changealtitude)
        if curr <= changealtitude:
            inc = True
        lat = self.vehicle.location.global_relative_frame.lat
        lon = self.vehicle.location.global_relative_frame.lon
        print(f"vehicle is at position lat: {lat}, lon: {lon}")
        print(f"Changing altitude to {changealtitude}")
        
        self.vehicle.simple_goto(LocationGlobalRelative(
            lat, lon,
            changealtitude,
        ))

        while True:
            newaltitude = self.vehicle.location.global_relative_frame.alt
            print("Altitude: ", newaltitude)
            if newaltitude >= changealtitude * 0.95 and inc:
                print(f"Reached new target altitude: {newaltitude}")
                break
            elif newaltitude <= (changealtitude + 0.5) and not inc:
                print(f"Reached new target altitude: {newaltitude}")
                break
            time.sleep(1)

    @cherrypy.expose
    def change_pos(self, lat, lon):
        initial_alt = self.vehicle.location.global_relative_frame.alt
        self.change_altitude(initial_alt + 8)
        print(f"Reached the altitude to change position")
        time.sleep(1)
        self.goto(lat, lon)
        print(f"Position changed")
        time.sleep(1)
        self.change_altitude(initial_alt)
        print(f"Driven back to initial altitude")
        return f"message: position change successful"

    @cherrypy.expose
    def align_yaw(self, yaw, relative=False):
        yaw = int(yaw)
        print(yaw)
        is_relative = 1 if relative else 0

        msg = self.vehicle.message_factory.command_long_encode(
            0, 0,
            mavutil.mavlink.MAV_CMD_CONDITION_YAW,
            0,
            yaw,
            0,
            1,
            is_relative,
            0, 0, 0
        )

        self.vehicle.send_mavlink(msg)
        timeout = 10
        start_time = time.time()
        while time.time() - start_time < timeout:
            newyaw = self.vehicle.heading
            print("yaw: ", newyaw)
            time.sleep(1)
        return f"yaw alignment successful {newyaw}"

    @cherrypy.expose
    def rtl(self):
        global flag
        print("Returning to launch")
        self.vehicle.mode = VehicleMode("RTL")

        while True:
            altitude = self.vehicle.location.global_relative_frame.alt
            print("Altitude: ", altitude)
            if altitude < 0.5 * 0.95:
                break
            time.sleep(1)
        flag = False
        print("RTL complete")
        return f"message: RTL successful"

    @cherrypy.expose
    def land(self):
        global flag
        print("Landing....")
        self.vehicle.mode = VehicleMode("LAND")

        while True:
            altitude = self.vehicle.location.global_relative_frame.alt
            print("Altitude: ", altitude)
            if altitude < 0.5 * 0.95:
                break
            time.sleep(1)
        flag = False
        print("Landing successful")
        return f"message: Landing successful"

def main():
    cherrypy_cors.install()
    vehicle = connect("COM31", baud=57600, wait_ready=False)
    cherrypy.server.socket_host = '0.0.0.0'
    cherrypy.server.socket_port = 8080

    cherrypy.config.update({
        'tools.encode.on': True, 'tools.encode.encoding': 'utf-8',
        'tools.decode.on': True,
        'tools.trailing_slash.on': True,
        'tools.staticdir.root': os.path.abspath(os.path.dirname(__file__)),
    })

    cherrypy.quickstart(Root(vehicle), '/', {
        '/': {
            'cors.expose.on': True,
        },
        '/media': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'static'
        }
    })  

if __name__ == '__main__':
    cherrypy_cors.install()
    # change the connection or port before running
    # vehicle = connect("COM13", baud=57600)
    #vehicle = connect("/dev/ttyUSB0", baud=57600)
    vehicle = connect("127.0.0.1:14550")
    cherrypy.server.socket_host = '0.0.0.0'
    cherrypy.server.socket_port = 8080

    cherrypy.config.update({
        'tools.encode.on': True, 'tools.encode.encoding': 'utf-8',
        'tools.decode.on': True,
        'tools.trailing_slash.on': True,
        'tools.staticdir.root': os.path.abspath(os.path.dirname(__file__)),
    })

    cherrypy.quickstart(Root(vehicle), '/', {
        '/': {
            'cors.expose.on': True,
        },
        '/media': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'static'
        }
    })