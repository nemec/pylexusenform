from typing import Dict
from xml.etree import ElementTree as et

import response_parsers as rp

class Command:
    def __init__(self, body: str, path: str, response_parser: rp.ResponseParser,
                 namespace: str = None, query: Dict = None, headers: Dict = None):
        if isinstance(body, et.Element):
            self.body = et.tostring(body)
        else:
            self.body = body
        self.path = path
        self.response_parser = response_parser
        self.namespace = namespace
        self.query = query
        self.headers = headers

class Commands:
    @staticmethod
    def __get_root():
        return et.Element('SPML')

    @staticmethod
    def __add_common(root, token, vin):
        common = et.SubElement(root, 'COMMON')

        auth = et.SubElement(common, 'AUTH')
        auth.set("REGION", "US")
        auth.text = token

        lang = et.SubElement(common, "LANG")
        lang.text = "en"

        version = et.SubElement(common, "VERSION")
        version.text = "Android"

        device = et.SubElement(common, "DEVICE")
        serial = et.SubElement(device, "SERIAL_NO")
        serial.text = "00000000"
        tel = et.SubElement(device, "TEL_NO")
        tel.text = "0000000000"
        dev_type = et.SubElement(device, "TYPE")
        dev_type.text = "Android"

        user = et.SubElement(common, "USER")
        user_id = et.SubElement(user, "USER_ID")
        user_id.text = vin

        et.SubElement(common, "SESSION")

    @staticmethod
    def __add_fake_position(root):
        position = et.SubElement(root, "POSITION")
        lat = et.SubElement(position, "LAT")
        lat.text = "0.000000"
        lon = et.SubElement(position, "LON")
        lon.text = "0.000000"
        acc = et.SubElement(position, "ACCURACY")
        acc.text = "65.000000"

    @staticmethod
    def __add_command(root, value):
        cmd = et.SubElement(root, "COMMAND")
        cmd.text = value

    @staticmethod
    def __add_config(root, key, value):
        cmd = et.SubElement(root, key)
        cmd.text = value

    @staticmethod
    def command_progress(token, vin, namespace):
        """Command for execution progress."""
        root = Commands.__get_root()
        Commands.__add_common(root, token, vin)
        Commands.__add_command(root, namespace)
        return Command(root,
                       "/get_remote_control_status_and_latest_info.aspx",
                       rp.ProgressParser,
                       namespace = namespace,
                       headers={
                           'Content-Type': 'text/plain charset=ISO-8859-1',
                           'Authorization': 'Bearer ' + token
                       })

    @staticmethod
    def vehicle_status(token, vin):
        """Command for vehicle status, locks, windows, etc."""
        root = Commands.__get_root()
        Commands.__add_common(root, token, vin)
        return Command(root,
                       "/get_realtime_status.aspx",
                       rp.StatusParser,
                       query={
                           'VIN': vin
                       },
                       headers={
                           'Content-Type': 'text/plain charset=ISO-8859-1',
                           'Authorization': 'Bearer ' + token
                       })

    @staticmethod
    def begin_refresh_vehicle_status(token, vin):
        """Command to start a vehicle status refresh"""
        ns = 'REALTIMESTATUSREQUEST'
        root = Commands.__get_root()
        Commands.__add_common(root, token, vin)
        Commands.__add_config(root, ns, '1')
        Commands.__add_fake_position(root)
        return Command(root,
                       "/remote_control.aspx",
                       rp.BasicCommandResponseParser,
                       namespace = ns,
                       query={
                           'command': 'VehicleRefresh',
                           'VIN': vin
                       },
                       headers={
                           'Authorization': 'Bearer ' + token
                       })

    @staticmethod
    def begin_lock_door(token, vin):
        """Command to start a vehicle door lock"""
        ns = 'DL'
        root = Commands.__get_root()
        Commands.__add_common(root, token, vin)
        Commands.__add_config(root, ns, '1')
        Commands.__add_fake_position(root)
        return Command(root,
                       "/remote_control.aspx",
                       rp.BasicCommandResponseParser,
                       namespace = ns,
                       query={
                           'command': 'DoorLock',
                           'VIN': vin
                       },
                       headers={
                           'Authorization': 'Bearer ' + token
                       })

    @staticmethod
    def begin_unlock_door(token, vin):
        """Command to start a vehicle door unlock"""
        ns = 'DL'
        root = Commands.__get_root()
        Commands.__add_common(root, token, vin)
        Commands.__add_config(root, ns, '2')
        Commands.__add_fake_position(root)
        return Command(root,
                       "/remote_control.aspx",
                       rp.BasicCommandResponseParser,
                       namespace = ns,
                       query={
                           'command': 'DoorLock',
                           'VIN': vin
                       },
                       headers={
                           'Authorization': 'Bearer ' + token
                       })

    @staticmethod
    def begin_remote_start(token, vin):
        """Command to start a vehicle"""
        ns = 'RES'
        root = Commands.__get_root()
        Commands.__add_common(root, token, vin)
        Commands.__add_config(root, ns, '1')
        Commands.__add_fake_position(root)
        return Command(root,
                       "/remote_control.aspx",
                       rp.BasicCommandResponseParser,
                       namespace = ns,
                       query={
                           'command': 'RemoteStart',
                           'VIN': vin
                       },
                       headers={
                           'Authorization': 'Bearer ' + token
                       })

    @staticmethod
    def begin_remote_stop(token, vin):
        """Command to stop a vehicle that was remotely started"""
        ns = 'RES'
        root = Commands.__get_root()
        Commands.__add_common(root, token, vin)
        Commands.__add_config(root, ns, '2')
        Commands.__add_fake_position(root)
        return Command(root,
                       "/remote_control.aspx",
                       rp.BasicCommandResponseParser,
                       namespace = ns,
                       query={
                           'command': 'RemoteStop',
                           'VIN': vin
                       },
                       headers={
                           'Authorization': 'Bearer ' + token
                       })