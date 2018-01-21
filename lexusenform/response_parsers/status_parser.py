import dateutil.parser as dp

import lexusenform.models as m
from lexusenform.timezone import TIMEZONE_MAPPING as tz
from .common import ResponseParser

class StatusParser(ResponseParser):
    """Return the status of the car"""

    def get_object(self):
        date = dp.parse(self.root.find("DATETIME").text, tzinfos=tz)
        dash = dp.parse(self.root.find("DASHBOARD_DATETIME").text, tzinfos=tz)

        odometer = None
        fuel_gague = None
        drive_range = None
        trip_a = None
        trip_b = None
        hazards_on = False

        doors = {
            'driver': m.Component("Driver Door"),
            'passenger': m.Component("Passenger Door"),
            'rear_passenger': m.Component("Rear Passenger Door"),
            'rear_driver': m.Component("Rear Driver Door")
        }
        windows = {
            'driver': m.Component("Driver Window"),
            'passenger': m.Component("Passenger Window"),
            'rear_passenger': m.Component("Rear Passenger Window"),
            'rear_driver': m.Component("Rear Driver Window")
        }
        other = {
            'hood': m.Component("Hood"),
            'trunk': m.Component("Trunk"),
            'sunroof': m.Component("Sunroof")
        }

        for item in self.root.findall('LIST/ITEM'):
            typ = item.find('TYPE')
            if typ is not None:
                typ = typ.text
            data = item.find('DATA')
            if data is not None:
                data = data.text
            unit = item.find('UNIT')
            if unit is not None:
                unit = unit.text
            safe = item.find('SECURITY')
            if safe is not None:
                safe = safe.text

            if typ == 'ODO':
                odometer = (float(data), unit)
            elif typ == 'FUGAGE':
                fuel_gague = (float(data), unit)
            elif typ == 'RAGE':
                drive_range = (float(data), unit)
            elif typ == 'TRIPA':
                trip_a = (float(data), unit)
            elif typ == 'TRIPB':
                trip_b = (float(data), unit)

            elif typ == 'DCTY':
                doors['driver'].closed = data == 'close'
                doors['driver'].safe = doors['driver'].safe and (safe == 'safe')
            elif typ == 'RLCY':
                doors['rear_driver'].closed = data == 'close'
                doors['rear_driver'].safe = doors['rear_driver'].safe and (safe == 'safe')
            elif typ == 'PCTY':
                doors['passenger'].closed = data == 'close'
                doors['passenger'].safe = doors['passenger'].safe and (safe == 'safe')
            elif typ == 'RRCY':
                doors['rear_passenger'].closed = data == 'close'
                doors['rear_passenger'].safe = doors['rear_passenger'].safe and (safe == 'safe')
            elif typ == 'HDCY':
                other['hood'].closed = data == 'close'
                other['hood'].safe = other['hood'].safe and (safe == 'safe')
            elif typ == 'LGCY':
                other['trunk'].closed = data == 'close'
                other['trunk'].safe = other['trunk'].safe and (safe == 'safe')
            elif typ == 'SRPOS':
                other['sunroof'].closed = data == 'close'
                other['sunroof'].safe = other['sunroof'].safe and (safe == 'safe')

            elif typ == 'LSWD':
                doors['driver'].locked = data == 'lock'
                doors['driver'].safe = doors['driver'].safe and (safe == 'safe')
            elif typ == 'LSWP':
                doors['passenger'].locked = data == 'lock'
                doors['passenger'].safe = doors['passenger'].safe and (safe == 'safe')
            elif typ == 'LSWR':
                doors['rear_passenger'].locked = data == 'lock'
                doors['rear_passenger'].safe = doors['rear_passenger'].safe and (safe == 'safe')
            elif typ == 'LSWL':
                doors['rear_driver'].locked = data == 'lock'
                doors['rear_driver'].safe = doors['rear_driver'].safe and (safe == 'safe')

            elif typ == 'PWDRD':
                windows['driver'].closed = data == 'close'
                windows['driver'].safe = windows['driver'].safe and (safe == 'safe')
            elif typ == 'PWDRL':
                windows['rear_driver'].closed = data == 'close'
                windows['rear_driver'].safe = windows['driver'].safe and (safe == 'safe')
            elif typ == 'PWDRP':
                windows['passenger'].closed = data == 'close'
                windows['passenger'].safe = windows['driver'].safe and (safe == 'safe')
            elif typ == 'PWDRR':
                windows['rear_passenger'].closed = data == 'close'
                windows['rear_passenger'].safe = windows['driver'].safe and (safe == 'safe')

            elif typ == 'HAZB':
                hazards_on = data != 'off'

        return m.VehicleStatus(
            date,
            dash,
            odometer,
            fuel_gague,
            drive_range,
            trip_a,
            trip_b,
            hazards_on,
            doors,
            windows,
            other)
