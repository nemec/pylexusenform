import requests
import json

class LexusRemote:
    LOGIN_URL = "https://telematicsservice.toyota.com/v1/authenticate"
    AUTH_URL = "https://telematicsservice.toyota.com/v1/authorize"
    OAUTH_URL = "https://api.telematics.net/v1/oauth2/token"
    REALTIME_STATUS_URL = "https://tscgt13cy01.g-book.com/keyoffservices/get_realtime_status.aspx"
    DOOR_LOCK_REQUEST_URL = "https://tscgt13cy01.g-book.com/keyoffservices/remote_control.aspx?command=DoorLock"
    REMOTE_CONTROL_STATUS_URL = "https://tscgt13cy01.g-book.com/keyoffservices/get_remote_control_status_and_latest_info.aspx"

    def __init__(self, config_file):
        self.config_file = config_file

    def login(self, username, password):
        pass
        # post LOGIN_URL
        # header "Accept", "application/json" "Content-Type", "application/json"
        # { "username": username, "password": password }
        resp = None
        val = json.loads(resp.content)
        # { "token": "asd", "tmsPasswordChangeFlag": "as" }
        return val.token
        
    def is_authorized(self, token):
        pass
        # post AUTH_URL
        # header "Accept", "application/json", "Content-Type", "application/json"

























