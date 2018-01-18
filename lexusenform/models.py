"""Various response models for a vehicle"""
from datetime import datetime
from enum import Enum
from typing import Tuple, List, Dict

class Component:
    def __init__(self, name: str):
        self.name = name
        self.closed = None
        self.locked = None
        self.safe = True

class VehicleStatus:
    '''Details on a vehicle's status'''
    def __init__(self,
                 last_updated_date: datetime,
                 dashboard_date: datetime,
                 odometer: Tuple[float, str],
                 fuel_gauge: Tuple[float, str],
                 drive_range: Tuple[float, str],
                 trip_a: Tuple[float, str],
                 trip_b: Tuple[float, str],
                 hazards_on: bool,
                 doors: Dict[str, Component],
                 windows: Dict[str, Component],
                 other: Dict[str, Component]):
        self.last_updated_date = last_updated_date
        self.dashboard_date = dashboard_date
        self.odometer = odometer
        self.fuel_gauge = fuel_gauge
        self.drive_range = drive_range
        self.trip_a = trip_a
        self.trip_b = trip_b
        self.hazards_on = hazards_on
        self.doors = doors
        self.windows = windows
        self.other = other

    def __str__(self):
        '''Stringify this'''
        ret = 'Last Updated: {}\n'.format(self.last_updated_date)
        ret += 'Odometer: {} {}\n'.format(self.odometer[0], self.odometer[1])
        ret += 'Fuel: {} {}\n'.format(self.fuel_gauge[0], self.fuel_gauge[1])
        ret += 'Doors:\n'
        for _, door in self.doors.items():
            ret += '  {}: '.format(door.name)
            if door.closed is True:
                ret += 'Closed'
            elif door.closed is False:
                ret += 'Open'
            if door.closed is not None and door.locked is not None:
                ret += ', '
            if door.locked is True:
                ret += 'Locked'
            elif door.closed is False:
                ret += 'Unlocked'
            ret += '\n'
        ret += 'Windows:\n'
        for _, door in self.windows.items():
            ret += '  {}: '.format(door.name)
            if door.closed is True:
                ret += 'Closed'
            elif door.closed is False:
                ret += 'Open'
            else:
                ret += 'Unknown'
            ret += '\n'
        return ret

class CommandStatus(Enum):
    '''Result status of a command execution'''
    OK = 1
    FAILED = 2

class BasicCommandResponse:
    '''Response details from a command request'''
    def __init__(self, code: str, timestamp: datetime = None):
        self.code = code
        if code == '011000':
            self.status = CommandStatus.OK
        else:
            self.status = CommandStatus.FAILED
        self.timestamp = timestamp

class ProgressStatus(Enum):
    '''Result status of a command execution'''
    IN_PROGRESS = 1
    COMPLETED = 2
    FAILED = 3
    UNKNOWN = 4

class ProgressResponse:
    '''Progress of a sent command'''

    OK_STATUS = ['SmsSent', 'WaitingDcmRequest', 'OnDcmExecuting']
    FAILED_CODE = ['211018']
    FINISHED_STATUS = 'NormalEnded'

    def __init__(self, code: str, vehicle_code: str, timestamp: datetime,
                 lat: float, lon: float, status: str, action: str,
                 progress: str, response_text: str = None):
        self.code = code
        self.vehicle_code = vehicle_code
        self.timestamp = timestamp
        self.location = (lat, lon)
        self.status = status
        self.action = action
        self.progress = progress
        if progress in self.OK_STATUS:
            self.command_status = ProgressStatus.IN_PROGRESS
        elif progress == self.FINISHED_STATUS:
            self.command_status = ProgressStatus.COMPLETED
        elif progress in self.FAILED_CODE:
            self.command_status = ProgressStatus.FAILED
        else:
            self.command_status = ProgressStatus.UNKNOWN
        self.response_text = response_text
