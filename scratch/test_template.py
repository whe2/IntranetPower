from fastapi.templating import Jinja2Templates
from fastapi import Request
import asyncio
from models import User, Employee

templates = Jinja2Templates(directory="templates")

# Mock request and user
class MockRequest:
    def __init__(self):
        self.url_for = lambda name, **path_params: "mock_url"
        self.scope = {"type": "http"}

user = User(
    full_name="Test User",
    role="admin",
    avatar_url=None,
    permissions="ver_directorio"
)
employees = [
    Employee(name="John", apellido="Doe", department="IT", email="john@test.com", photo_url=None)
]

try:
    templates.get_template("directorio.html").render({"request": MockRequest(), "user": user, "employees": employees})
    print("Render successful!")
except Exception as e:
    import traceback
    traceback.print_exc()
