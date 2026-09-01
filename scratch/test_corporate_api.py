import urllib.request
import urllib.parse
import json
import time

def test_corporate_export():
    login_url = "https://powerlink.rubpi.com/api/login"
    creds = {"username": "api_exp", "password": "-?J+\\FcmKT2zWl5A28=~"}
    data = json.dumps(creds).encode('utf-8')

    req = urllib.request.Request(login_url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req) as response:
        res_data = json.loads(response.read().decode())
        api_token = res_data.get('token') or res_data.get('access_token')

    print("Token obtained successfully.")

    # Try different filter formats for is_natural=false
    # Format 1: ?filters={"is_natural":false} (JSON urlencoded)
    # Format 2: ?filters=is_natural=false or ?is_natural=false
    filter_options = [
        ("JSON urlencode", f"https://powerlink.rubpi.com/api/exports/users?filters={urllib.parse.quote(json.dumps({'is_natural': False}))}"),
        ("JSON string", 'https://powerlink.rubpi.com/api/exports/users?filters={"is_natural":false}'),
        ("Query param is_natural", "https://powerlink.rubpi.com/api/exports/users?is_natural=false"),
        ("Filters is_natural=false", "https://powerlink.rubpi.com/api/exports/users?filters=is_natural=false"),
        ("POST body filters", "https://powerlink.rubpi.com/api/exports/users")
    ]

    for label, url in filter_options:
        print(f"\nTesting {label}: {url}")
        body = None
        if label == "POST body filters":
            body = json.dumps({"filters": {"is_natural": False}}).encode('utf-8')
        
        req2 = urllib.request.Request(
            url, 
            data=body,
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
                task_id = res2_data.get('task_id') or res2_data.get('id')
                print(f"-> SUCCESS! Task ID: {task_id}, Response: {res2_data}")
                
                # Check status
                if task_id:
                    get_url = f"https://powerlink.rubpi.com/api/exports/users/{task_id}"
                    for i in range(5):
                        time.sleep(2)
                        req3 = urllib.request.Request(get_url, headers={'Authorization': f'Bearer {api_token}'}, method='GET')
                        try:
                            with urllib.request.urlopen(req3) as resp3:
                                res3_data = json.loads(resp3.read().decode())
                                users = res3_data.get('data', [])
                                print(f"Task status: {res3_data.get('status')}, Users count: {len(users)}")
                                if users:
                                    print("Sample user:", users[0].get('name'), "| doc:", users[0].get('doc_type'), users[0].get('doc'), "| Plan:", users[0].get('plan'))
                                break
                        except urllib.error.HTTPError as e:
                            if e.code == 400:
                                print(f"Waiting for task ({e.code})...")
                                continue
                            print(f"Error {e.code}")
                            break
                    break
        except urllib.error.HTTPError as e:
            err_body = e.read().decode() if hasattr(e, 'read') else ''
            print(f"-> FAILED ({e.code}): {err_body}")
        except Exception as e:
            print(f"-> ERROR: {str(e)}")

if __name__ == "__main__":
    test_corporate_export()
