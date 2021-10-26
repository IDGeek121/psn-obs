import urllib.request
import urllib.parse
import urllib.error
import json

# Takes an npsso for a given PSN account, and returns an OAuth token for querying the Trophy API.
# To get your npsso, perform the following steps:
# 1. Log into your PSN account on https://www.playstation.com/
# 2. Go to https://ca.account.sony.com/api/v1/ssocookie and copy the npsso value.
def get_psn_token(npsso: str) -> str:
    if not npsso:
        return ''
    url = 'https://ca.account.sony.com/api/authz/v3/oauth/authorize?access_type=offline&client_id=ac8d161a-d966-4728-b0ea-ffec22f69edc&redirect_uri=com.playstation.PlayStationApp%3A%2F%2Fredirect&response_type=code&scope=psn%3Amobile.v1%20psn%3Aclientapp'
    # With a valid npsso, this will catch. This GET is done to get the 'code' for the POST below.
    try:
        request = urllib.request.Request(url)
        request.add_header('Cookie', f'npsso={npsso}')
        urllib.request.urlopen(request)
        print('Error: Check npsso')
    except urllib.error.HTTPError as err:
        redirect = err.filename
        if '?code=v3' in redirect:
            query_string = urllib.parse.urlparse(redirect).query
            query = urllib.parse.parse_qs(query_string)
        else:
            print('Error: Check npsso')

    # This request gets the actual token
    data = {
        'code': query['code'][0],
        'redirect_uri': 'com.playstation.PlayStationApp://redirect',
        'grant_type': 'authorization_code',
        'token_format': 'jwt',
    }
    data = urllib.parse.urlencode(data).encode('ascii')
    headers = {
        'Authorization': 'Basic YWM4ZDE2MWEtZDk2Ni00NzI4LWIwZWEtZmZlYzIyZjY5ZWRjOkRFaXhFcVhYQ2RYZHdqMHY=',
    }
    url = 'https://ca.account.sony.com/api/authz/v3/oauth/token'

    token_request = urllib.request.Request(url, headers=headers, data=data)
    with urllib.request.urlopen(token_request) as f:
        response_text = f.read()
    response_json = json.loads(response_text)
    return response_json['access_token']

def _get(url: str, token: str) -> dict:
    headers = {
        'Authorization': f'Bearer {token}',
        'User-agent': 'funnyagent',
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as f:
        resp = f.read()
    return json.loads(resp)

def get_trophy_titles(token: str) -> dict:
    url = 'https://m.np.playstation.net/api/trophy/v1/users/me/trophyTitles'
    return _get(url, token)

def get_trophies_for_title(token: str, trophy_title: dict) -> dict:
    url = f'https://m.np.playstation.net/api/trophy/v1/npCommunicationIds/{trophy_title["npCommunicationId"]}/trophyGroups/all/trophies'
    data = {
        'npServiceName': trophy_title['npServiceName'],
    }
    data = urllib.parse.urlencode(data)
    return _get(f'{url}?{data}', token)

def get_trophies_earned_for_title(token: str, trophy_title: dict) -> dict:
    url = f'https://m.np.playstation.net/api/trophy/v1/users/me/npCommunicationIds/{trophy_title["npCommunicationId"]}/trophyGroups/all/trophies'
    data = {
        'npServiceName': trophy_title['npServiceName'],
    }
    data = urllib.parse.urlencode(data)
    return _get(f'{url}?{data}', token)

def get_trophy_earned_for_title(token: str, trophy_title: dict, trophy_id: int):
    url = f'https://m.np.playstation.net/api/trophy/v1/users/me/npCommunicationIds/{trophy_title["npCommunicationId"]}/trophyGroups/all/trophies'
    data = {
        'npServiceName': trophy_title['npServiceName'],
        'limit': 1,
        'offset': trophy_id,
    }
    data = urllib.parse.urlencode(data)
    return _get(f'{url}?{data}', token)
    