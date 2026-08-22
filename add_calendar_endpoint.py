import re

filepath = r"c:\Users\wgallardo\Documents\Proyectos gravity\intranet\main.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

new_endpoints = """
@app.get("/api/intranet/calendar")
async def get_calendar_events(
    year: int = Query(...),
    month: int = Query(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    # Fetch events
    events = db.query(models.CalendarEvent).filter(
        models.CalendarEvent.year == year,
        models.CalendarEvent.month == month
    ).all()
    
    # Fetch birthdays for this month (we look at all employees with a birthday)
    employees = db.query(models.Employee).filter(models.Employee.birthday_date != None, models.Employee.birthday_date != "").all()
    birthdays = []
    for emp in employees:
        try:
            bday = datetime.strptime(emp.birthday_date, '%Y-%m-%d').date()
            if bday.month == month:
                birthdays.append({
                    "day": bday.day,
                    "name": emp.full_name if hasattr(emp, 'full_name') else f"{emp.name} {emp.apellido or ''}".strip(),
                    "photo_url": emp.photo_url or "/static/img/default-avatar.png",
                    "department": emp.department
                })
        except:
            pass
            
    # Structure data by day
    days_data = {}
    
    for ev in events:
        if ev.day not in days_data:
            days_data[ev.day] = {"events": [], "birthdays": []}
        days_data[ev.day]["events"].append({
            "id": ev.id,
            "title": ev.title,
            "description": ev.description
        })
        
    for b in birthdays:
        if b["day"] not in days_data:
            days_data[b["day"]] = {"events": [], "birthdays": []}
        days_data[b["day"]]["birthdays"].append(b)
        
    return days_data

"""

if "/api/intranet/calendar" not in content:
    target = 'if __name__ == "__main__":'
    if target in content:
        content = content.replace(target, new_endpoints + "\n" + target)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print("Success: Backend calendar endpoint added to main.py")
    else:
        print("Error: Could not find target in main.py")
else:
    print("Endpoint already exists.")
