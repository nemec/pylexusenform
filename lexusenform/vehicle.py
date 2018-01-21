"""Vehicle data"""
from datetime import timedelta
import json
import time

from .commands import Commands as c
from .models import ProgressStatus
from lexusenform import AccountError


class Vehicle:
    """Vehicle data"""

    def __init__(self, vehicle_id, partial_vin, full_vin, make, model, year, extra_data=None):
        self.vehicle_id = vehicle_id
        self.partial_vin = partial_vin
        self.full_vin = full_vin
        self.make = make
        self.model = model
        self.year = year
        self.extra_data = extra_data
        self._account = None

    def set_account(self, account):
        '''Bind an account to this vehicle'''
        self._account = account

    def ensure_vin(self):
        '''
        Ensure the full VIN is set, since the API
        does not allow us to retrieve the full value
        '''
        if self.full_vin is None:
            raise AccountError(
                "Full vin is missing from this vehicle. Please add by calling "
                "account.add_vin_mapping('{vehicle_id}', {{vin}})".format(vehicle_id=self.vehicle_id))

    def __process_until_finished(self,
                                 namespace: str,
                                 vehicle_code: str = None,
                                 sleep: timedelta = timedelta(seconds=5),
                                 timeout: timedelta = timedelta(minutes=3)):
        '''Check progress on command until it's finished. Optionally, wait for vehicle code'''
        tok = self._account.get_id_token()
        prog_c = c.command_progress(tok, self.full_vin, namespace)
        expires = time.time() + timeout.total_seconds()
        while True:
            prog = self._account.execute(prog_c)
            if (prog.command_status == ProgressStatus.COMPLETED and
                    (vehicle_code is None or
                     prog.vehicle_code == vehicle_code)):
                break
            if (prog.command_status == ProgressStatus.FAILED or
                    prog.command_status == ProgressStatus.UNKNOWN):
                if prog.progress is not None:
                    raise AccountError(
                        "Processing of command failed with value {}".format(prog.progress))
                else:
                    raise AccountError("Processing of command failed:\n{}".format(prog.response_text))
            if time.time() > expires:
                raise AccountError("Command timed out without completing")
            if self._account.DEBUG:
                if prog.progress is not None:
                    print("Progress: {}".format(prog.progress))
                else:
                    print("Progress:\n{}".format(prog.response_text))
                if prog.vehicle_code is not None:
                    print("Vehicle code: {}".format(prog.vehicle_code))
            time.sleep(sleep.total_seconds())


    def status(self, force_refresh=False):
        '''
        Retrieve the status of the car's components.
        This includes window and door status, as well
        as odometer and fuel readings.
        '''
        self.ensure_vin()
        tok = self._account.get_id_token()

        if force_refresh:
            cmd = c.begin_refresh_vehicle_status(tok, self.full_vin)
            self._account.execute(cmd)
            self.__process_until_finished(cmd.namespace)

        cmd = c.vehicle_status(tok, self.full_vin)
        return self._account.execute(cmd)


    def lock_doors(self):
        '''Lock the car's doors'''
        self.ensure_vin()
        tok = self._account.get_id_token()
        cmd = c.begin_lock_door(tok, self.full_vin)
        self._account.execute(cmd)

        self.__process_until_finished(cmd.namespace, vehicle_code='01')
        # Code of D9 means doors already locked??

        return True


    def unlock_doors(self):
        '''Unlock the car's doors'''
        self.ensure_vin()
        tok = self._account.get_id_token()
        cmd = c.begin_unlock_door(tok, self.full_vin)
        self._account.execute(cmd)

        self.__process_until_finished(cmd.namespace, vehicle_code='01')

        return True


    def remote_start(self):
        '''Remotely start the car'''
        self.ensure_vin()
        tok = self._account.get_id_token()
        cmd = c.begin_remote_start(tok, self.full_vin)
        self._account.execute(cmd)

        self.__process_until_finished(cmd.namespace, vehicle_code='01')

        return True


    def remote_stop(self):
        '''Turn off the car if it was remotely started'''
        self.ensure_vin()
        tok = self._account.get_id_token()
        cmd = c.begin_remote_stop(tok, self.full_vin)
        self._account.execute(cmd)

        self.__process_until_finished(cmd.namespace, vehicle_code='01')

        return True





class VehicleEncoder(json.JSONEncoder):
    """Serialize a Vehicle"""

    def default(self, obj):  # pylint: disable=E0202,W0221
        if isinstance(obj, Vehicle):
            return {
                '__type__': 'Vehicle',
                'vehicle_id': obj.vehicle_id,
                'partial_vin': obj.partial_vin,
                'full_vin': obj.full_vin,
                'make': obj.make,
                'model': obj.model,
                'year': obj.year,
                'extra_data': obj.extra_data
            }
        return json.JSONEncoder.default(self, obj)

class VehicleDecoder(json.JSONDecoder):
    """Deserialize a list of vehicles"""

    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.hook, *args, **kwargs)

    def hook(self, obj):
        """Deserialize a list of vehicles"""

        if '__type__' in obj and obj['__type__'] == 'Vehicle':
            return Vehicle(
                obj['vehicle_id'],
                obj.get('partial_vin'),
                obj.get('full_vin'),
                obj['make'],
                obj['model'],
                obj['year'],
                obj['extra_data'])
        return obj
