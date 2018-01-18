from urllib.parse import urlsplit, parse_qs
from xml.etree import ElementTree as et
import requests
import base64
import json

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

username = "dan@nem.ec"
password = "Skweezle90-"
vin = "JTHBE1D27F501939220160805154951"


enform_policy = "B2C_1_TMNA_TSC_SXM_LER_SignInPolicy"
client_id = "5004e6b3-5880-4fda-ae71-219d53e74988"
redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
scope = "profile offline_access openid"

s = requests.Session()


def request_new_token():
    auth = s.get("https://login.microsoftonline.com/tmnab2c.onmicrosoft.com/oauth2/v2.0/authorize",
        params={
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": scope,
            "prompt": "login",
            "p": enform_policy,
            "response_mode": "query"
        })

    claims = json.loads(base64.b64decode(auth.cookies["x-ms-cpim-trans"]).decode("utf-8"))
    tid = claims["T_DIC"][0]["I"]


    s.post("https://login.microsoftonline.com/tmnab2c.onmicrosoft.com/B2C_1_TMNA_TSC_SXM_LER_SignInPolicy/SelfAsserted?tx=StateProperties={}&p={}"
            .format(base64.b64encode(bytes('{"TID":"' + tid + '"}', 'utf-8')).decode("utf-8"),
                    enform_policy),
        data={
            "request_type": "RESPONSE",
            "logonIdentifier": username,
            "password": password
        },
        headers={
            "X-CSRF-TOKEN": auth.cookies["x-ms-cpim-csrf"],
            "Origin": "https://login.microsoftonline.com"
        })



    n = s.get("https://login.microsoftonline.com/tmnab2c.onmicrosoft.com/{0}/api/CombinedSigninAndSignup/confirmed?csrf_token={1}&tx=StateProperties={2}&p={0}"
        .format(enform_policy,
                auth.cookies["x-ms-cpim-csrf"],
                base64.b64encode(bytes('{"TID":"' + tid + '"}', 'utf-8')).decode("utf-8")),
        allow_redirects=False)


    urn = n.headers["Location"]
    if 'error' in urn:
        raise ValueError(urn)
        
    query = parse_qs(urlsplit(urn).query)
    auth_code = query['code'][0]

    tok = s.post("https://login.microsoftonline.com/tmnab2c.onmicrosoft.com/oauth2/v2.0/token",
        params={
            'p': enform_policy
        },
        data={
            "grant_type": "authorization_code",
            "code": auth_code,
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "p": enform_policy
        })
        
    return tok.json()


def save_tokens(filename, tokens):
    with open(filename, 'w') as f:
        json.dump(tokens, f, sort_keys=True, indent=4)


def refresh_new_token(refresh_token):
    tok = s.post("https://login.microsoftonline.com/tmnab2c.onmicrosoft.com/oauth2/v2.0/token",
        params={
            "p": enform_policy
        },
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "p": enform_policy
        })
        
    """{
        "error": "invalid_grant", 
        "error_description": "AADB2C90080: The provided grant has expired. Please re-authenticate and try again. Current time: 1514443053, Grant issued time: 1513480069, Grant expiration time: 1516072069\r\nCorrelation ID: 1cb64b4c-2ffd-4f43-a445-7771c98339bf\r\nTimestamp:
    2017-12-28 06:37:33Z\r\n"
    }"""
        
    return tok.json()




def get_status(token, vin):
    root = et.Element('SPML')
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
    
    data = et.tostring(root)
    
    req = requests.post("https://tscgt13cy01.g-book.com/keyoffservices/get_realtime_status.aspx",
        params={
            'VIN': vin
        },
        data=data,
        headers={
            'Content-Type': 'text/plain',
            'Authorization': 'Bearer ' + token
        })
    
    
    #not logged in
    # <?xml version="1.0" encoding="utf-8"?><SPML><RESULT><CODE>111012</CODE></RESULT></SPML>
    return req.text


def remote_start(token, vin):
    root = et.Element('SPML')
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
    
    res = et.SubElement(root, "RES")
    res.text = "1"
    
    position = et.SubElement(root, "POSITION")
    lat = et.SubElement(position, "LAT")
    lat.text = "0.000000"
    lon = et.SubElement(position, "LON")
    lon.text = "0.000000"
    acc = et.SubElement(position, "ACCURACY")
    acc.text = "65.000000"
    
    data = et.tostring(root)
    
    req = requests.post("https://tscgt13cy01.g-book.com/keyoffservices/remote_control.aspx",
        params={
            'command': 'RemoteStart',
            'VIN': vin
        },
        data=data,
        headers={
            'Authorization': 'Basic ZGpuZW1lYzo='
        })
        
    return req.text



if __name__ == "__main__":
    filename = 'enform-token.json'
    try:
        with open(filename, 'r') as f:
            tokens = json.load(f)
    except IOError: 
        print("Requesting new token...")
        tokens = request_new_token()
        save_tokens(filename, tokens)

    
    #new = refresh_new_token(tokens['refresh_token'])
    #save_tokens(filename, new)
    #print(get_status(tokens['id_token'], vin))
    print(remote_start(tokens['id_token'], vin))
