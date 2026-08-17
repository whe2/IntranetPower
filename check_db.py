from database import engine
from sqlalchemy import text
import pprint

with engine.connect() as c:
    u = c.execute(text('SELECT * FROM users LIMIT 1')).mappings().first()
    pprint.pprint(dict(u) if u else "No users")
    
    e = c.execute(text('SELECT * FROM employees LIMIT 1')).mappings().first()
    pprint.pprint(dict(e) if e else "No employees")
