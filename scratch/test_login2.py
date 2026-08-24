import urllib.request
import urllib.parse
import json

# Login
url = 'http://127.0.0.1:8000/api/auth/login'
data = urllib.parse.urlencode({'username': 'admin', 'password': 'Admin123!'}).encode('utf-8')
req = urllib.request.Request(url, data=data)
try:
    response = urllib.request.urlopen(req)
    headers = response.headers
    cookie = headers.get('Set-Cookie')
    if cookie:
        cookie = cookie.split(';')[0]
    else:
        print("No cookie received")
        exit(1)
    
    # Access directorio
    req2 = urllib.request.Request('http://127.0.0.1:8000/directorio')
    req2.add_header('Cookie', cookie)
    res2 = urllib.request.urlopen(req2)
    print("Success, status code:", res2.status)
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code}")
    print(e.read().decode('utf-8'))
except Exception as e:
    print(f"Error: {e}")
