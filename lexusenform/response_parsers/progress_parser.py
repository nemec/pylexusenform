import dateutil.parser as dp

import models as m
from timezone import TIMEZONE_MAPPING as tz
from .common import ResponseParser

class ProgressParser(ResponseParser):
    """Parses a response code from the server"""

    def get_object(self):
        code = self.root.find("RESULT/CODE").text

        vehicle_code = None
        vehicle_code_elem = self.root.find("RESULT/VEHICLE_RESULT_CODE")
        if vehicle_code_elem is not None:
            vehicle_code = vehicle_code_elem.text
        # D9 - finally complete
        # D0 - unknown?

        timestamp = None
        ts_elem = self.root.find(self.namespace + "/DATE")
        if ts_elem is not None:
            timestamp = dp.parse(ts_elem.text, tzinfos=tz)

        lat = None
        lat_elem = self.root.find("LAT")
        if lat_elem is not None:
            lat = float(lat_elem.text)
        lon = None
        lon_elem = self.root.find("LON")
        if lon_elem is not None:
            lon = float(lon_elem.text)

        status = None
        status_elem = self.root.find(self.namespace + "/STATUS")
        if status_elem is not None:
            status = status_elem.text

        action = None
        action_elem = self.root.find(self.namespace + "/ACTION")
        if action_elem is not None:
            action = action_elem.text

        progress = None
        progress_elem = self.root.find(self.namespace + "/PROGRESS")
        if progress_elem is not None:
            progress = progress_elem.text
        # SmsSent
        # WaitingDcmRequest
        # OnDcmExecuting
        # NormalEnded

        return m.ProgressResponse(
            code, vehicle_code, timestamp, lat, lon,
            status, action, progress, self.response_text)
