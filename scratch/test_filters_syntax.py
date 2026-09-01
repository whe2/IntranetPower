import urllib.request
import urllib.parse
import json
import time

def test_corporate_filters():
    login_url = "https://powerlink.rubpi.com/api/login"
    creds = {"username": "api_exp", "password": "-?J+\\FcmKT2zWl5A28=~"}
    data = json.dumps(creds).encode('utf-8')

    req = urllib.request.Request(login_url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req) as response:
        res_data = json.loads(response.read().decode())
        api_token = res_data.get('token') or res_data.get('access_token')

    tests = [
        "https://powerlink.rubpi.com/api/exports/users?is_natural=false",
        "https://powerlink.rubpi.com/api/exports/users?filters=is_natural=false",
        "https://powerlink.rubpi.com/api/exports/users?filters=is_natural:false",
    ]

    for url in tests:
        print(f"\nTesting: {url}")
        req2 = urllib.request.Request(
            url,
            headers={
                'Authorization': f'Bearer {api_token}', 
                'Content-Type': 'application/json', 
                'Accept': 'application/json'
            }, 
            method='POST'
        )
        try:
            with urllib.request.urlopen(req2) as response:
                res2_data = json.loads(response.read().decode())
                print(f"Response: {res2_data}")
        except urllib.error.HTTPError as e:
            err_body = e.read().decode() if hasattr(e, 'read') else ''
            print(f"Failed ({e.code}): {err_body}")

if __name__ == "__main__":
    test_corporate_filters()
