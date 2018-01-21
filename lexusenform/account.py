"""Represents an active account with the Lexus Enform service"""
import base64
import json
import time
from urllib.parse import urlsplit, parse_qs

import requests

from .commands import Command
import lexusenform.jwt as jwt
from .vehicle import Vehicle, VehicleEncoder, VehicleDecoder


def pretty_print(req):
    """
    At this point it is completely built and ready
    to be fired; it is "prepared".

    However pay attention at the formatting used in 
    this function because it is programmed to be pretty 
    printed and may differ from the actual request.
    """
    print('{}\n{}\n{}\n\n{}'.format(
        '-----------START-----------',
        req.method + ' ' + req.url,
        '\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
        req.body,
    ))


class Account:
    """Represents an active account with the Lexus Enform service"""
    AUTHORIZATION_BASE_URL = "https://login.microsoftonline.com/tmnab2c.onmicrosoft.com"
    AUTHORIZATION_URL = AUTHORIZATION_BASE_URL + "/oauth2/v2.0/authorize"

    POLICY_URL_FORMAT = AUTHORIZATION_BASE_URL + "/{policy}/SelfAsserted"
    # The weird multiple equals in a single query param is intentional, for some reason.
    POLICY_QUERY_FORMAT = "?tx=StateProperties={tid}&p={policy}"

    AUTH_CODE_URL_FORMAT = AUTHORIZATION_BASE_URL + "/{policy}/api/CombinedSigninAndSignup/confirmed"
    AUTH_CODE_QUERY_FORMAT = "?csrf_token={csrf}&tx=StateProperties={tid}&p={policy}"

    TOKEN_URL = AUTHORIZATION_BASE_URL + "/oauth2/v2.0/token"

    EXCHANGE_URL = "https://mobile.telematics.net/as/exchangeToken"
    ACCOUNT_URL_FORMAT = "https://prd.api.telematics.net/m/subscription/accounts/{guid}/vehicles"

    COMMAND_BASE_URL = "https://tscgt13cy01.g-book.com/keyoffservices"

    CACHE_ID_KEY = 'id_token'
    CACHE_ID_EXPIRES = 'id_expires'
    CACHE_REFRESH_KEY = 'refresh_token'
    CACHE_REFRESH_EXPIRES = 'refresh_expires'

    EXPIRE_SECONDS_BUFFER = 15


    ENFORM_POLICY = "B2C_1_TMNA_TSC_SXM_LER_SignInPolicy"
    CLIENT_ID = "5004e6b3-5880-4fda-ae71-219d53e74988"
    REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"
    SCOPE = "profile offline_access openid"

    DEBUG = True

    def __init__(self, email: str, password: str, config_file: str = None):
        self.email = email
        self.password = password
        self.config_file = config_file

        self._token_cache = self._load_from_config() or {}
        if 'vehicles' in self._token_cache:
            for veh in self._token_cache['vehicles']:
                veh.set_account(self)
        self._disable_config_file = False


    def _load_from_config(self):
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f, cls=VehicleDecoder)
        except IOError:
            return None

    def _save_cache(self):
        if not self._disable_config_file:  # when it is not accessible, skip
            try:
                with open(self.config_file, 'w') as f:
                    json.dump(self._token_cache, f, sort_keys=True, indent=4, cls=VehicleEncoder)
                    return True
            except IOError:
                self._disable_config_file = True
                return False

    def get_id_token(self):
        cache = self._token_cache
        if cache and self.CACHE_ID_KEY in cache:
            tok = cache[self.CACHE_ID_KEY]
            if jwt.token_is_expired(tok):
                toks = self._refresh_id_token()
                return toks[self.CACHE_ID_KEY]
            return tok
        toks = self._request_new_tokens()
        return toks[self.CACHE_ID_KEY]

    def _refresh_id_token(self):
        cache = self._token_cache
        if cache:
            refresh_token = cache[self.CACHE_REFRESH_KEY]
            expire_time = cache[self.CACHE_REFRESH_EXPIRES]
            if time.time() > expire_time:  # refresh token expired
                toks = self._request_new_tokens()
                return toks[self.CACHE_ID_KEY]
            tok = requests.post(self.TOKEN_URL,
                params={
                    "p": self.ENFORM_POLICY
                },
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": self.CLIENT_ID,
                    "redirect_uri": self.REDIRECT_URI,
                    "scope": self.SCOPE,
                    "p": self.ENFORM_POLICY
                })

            resp = tok.json()
            if "error" in resp:
                if "error_description" in resp:
                    raise ValueError("Refresh failure: {}".format(
                        resp["error_description"]
                    ))
                raise ValueError("Refresh failure: {}".format(
                    tok.content
                ))

            cache[self.CACHE_ID_KEY] = resp[self.CACHE_ID_KEY]
            cache[self.CACHE_ID_EXPIRES] = resp['id_token_expires_in'] + int(time.time())
            self._save_cache()

            return resp


    def _request_new_tokens(self):
        sess = requests.Session()

        auth = sess.get(self.AUTHORIZATION_URL,
            params={
                "client_id": self.CLIENT_ID,
                "response_type": "code",
                "redirect_uri": self.REDIRECT_URI,
                "scope": self.SCOPE,
                "prompt": "login",
                "p": self.ENFORM_POLICY,
                "response_mode": "query"
            })

        csrf = auth.cookies["x-ms-cpim-csrf"]

        claims = json.loads(base64.b64decode(auth.cookies["x-ms-cpim-trans"]).decode("utf-8"))
        tid = claims["T_DIC"][0]["I"]
        tid = base64.b64encode(bytes('{"TID":"' + tid + '"}', 'utf-8')).decode("utf-8")

        # send policy login request. For some reason, the response is never used
        sess.post((self.POLICY_URL_FORMAT + self.POLICY_QUERY_FORMAT)
                .format(tid=tid, policy=self.ENFORM_POLICY),
            data={
                "request_type": "RESPONSE",
                "logonIdentifier": self.email,
                "password": self.password
            },
            headers={
                "X-CSRF-TOKEN": csrf,
                "Origin": "https://login.microsoftonline.com"
            })


        code_req = sess.get((self.AUTH_CODE_URL_FORMAT + self.AUTH_CODE_QUERY_FORMAT)
            .format(
                policy=self.ENFORM_POLICY,
                csrf=csrf,
                tid=tid),
            allow_redirects=False)

        urn = code_req.headers["Location"]
        if 'error' in urn:
            raise ValueError(urn)

        query = parse_qs(urlsplit(urn).query)
        auth_code = query['code'][0]

        tok_req = sess.post(self.TOKEN_URL,
            params={
                'p': self.ENFORM_POLICY
            },
            data={
                "grant_type": "authorization_code",
                "code": auth_code,
                "client_id": self.CLIENT_ID,
                "redirect_uri": self.REDIRECT_URI,
                "scope": self.SCOPE,
                "p": self.ENFORM_POLICY
            })

        toks = tok_req.json()
        if not self.CACHE_ID_KEY in toks:
            raise ValueError("Refresh failure: {}".format(tok_req.text))

        cache = self._token_cache
        cache[self.CACHE_ID_KEY] = toks[self.CACHE_ID_KEY]
        cache[self.CACHE_ID_EXPIRES] = (toks['id_token_expires_in'] + int(time.time())
                                        - self.EXPIRE_SECONDS_BUFFER)
        cache[self.CACHE_REFRESH_KEY] = toks[self.CACHE_REFRESH_KEY]
        cache[self.CACHE_REFRESH_EXPIRES] = (toks['refresh_token_expires_in'] + int(time.time())
                                             - self.EXPIRE_SECONDS_BUFFER)
        self._save_cache()
        return toks


    #http://maps.googleapis.com/maps/api/geocode/json?latlng=29.9878772,-95.5485734


    def add_vin_mapping(self, vehicle_id, vin):
        cache = self._token_cache
        if 'mappings' not in cache:
            cache['mappings'] = {}
        cache['mappings'][vehicle_id] = vin
        self._save_cache()

    def execute(self, command: Command):
        """Execute a command"""
        req = requests.post('{}{}'.format(self.COMMAND_BASE_URL, command.path),
            params=command.query,
            headers=command.headers,
            data=command.body)
        if self.DEBUG is True:
            print(pretty_print(req.request))

        if not req.status_code == 200:
            raise ValueError("Command failed: {}".format(req.text))

        parser = command.response_parser(req.text, command.namespace)
        return parser.get_object()

    def vehicles(self, force_refresh: bool = False) -> Vehicle:
        """Retrieve the list of vehicles from the account"""

        cache = self._token_cache

        if not force_refresh and 'vehicles' in cache:
            return cache['vehicles']

        tok = self.get_id_token()
        exch = requests.post(self.EXCHANGE_URL,
            headers={
                'CV-TSP': 'LEXUS_17CY',  # 16CY and 18CY don't work... yet?
                'CV-OS-VERSION': '7.0',
                'CV-OS-TYPE': 'Android',
                'Authorization': 'Bearer {}'.format(tok)
            })

        if not exch.status_code == 200:
            raise ValueError("Invalid response from exchange: {}".format(exch.text))

        access_token = exch.json()['access_token']
        apikey = exch.headers['CV-APIKey']
        guid = exch.headers['GUID']

        veh_req = requests.get(self.ACCOUNT_URL_FORMAT.format(guid=guid),
            params={
                "view": "SUMMARY",
                "role": "REMOTECMD_USER",
                "timeZone": "utc",
                "timeFormat": "custom"
            },
            headers={
                'CV-ApiKey': apikey,
                'CV-AppType': 'MOBILE',
                'Authorization': 'Bearer {}'.format(access_token)
            })

        if not veh_req.status_code == 200:
            raise ValueError("Invalid response from account: {}".format(veh_req.text))

        ret = []
        for item in veh_req.json():
            full_vin = cache.get("mappings", None).get(item['id'], None)
            veh = Vehicle(item['id'], item['vin'], full_vin,
                item['makeName'], item['modelName'], item['modelYear'],
                extra_data=item)
            veh.set_account(self)
            ret.append(veh)

        cache['vehicles'] = ret
        self._save_cache()
        return ret

    def vehicle(self, vin: str, force_refresh: bool = False) -> Vehicle:
        """Find a vehicle by its VIN"""
        veh = self.vehicles(force_refresh)
        for v in veh:
            if vin == v.full_vin or vin.startswith(v.partial_vin):
                return v
        return None
