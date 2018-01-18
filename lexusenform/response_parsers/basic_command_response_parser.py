import dateutil.parser as dp

import models as m
from timezone import TIMEZONE_MAPPING as tz
from .common import ResponseParser

class BasicCommandResponseParser(ResponseParser):
    """Parses a response code from the server"""

    def get_object(self):
        code = self.root.find("RESULT/CODE").text
        date_elem = self.root.find("RESULT/DATETIME")
        timestamp = None
        if date_elem is not None:
            timestamp = dp.parse(date_elem.text, tzinfos=tz)

        return m.BasicCommandResponse(code, timestamp)
