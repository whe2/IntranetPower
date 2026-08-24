import requests

session = requests.Session()
# Assuming there is a test user or admin user, or we can just create one or use login endpoint
# Let's try logging in. Wait, what are the credentials?
# credenciales.txt is available
with open('credenciales.txt', 'r') as f:
    print(f.read())
