import re

filepath = r"c:\Users\wgallardo\Documents\Proyectos gravity\intranet\main.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

new_endpoints = """
@app.post("/api/rrhh/calendar_events")
async def add_calendar_event(
    title: str = Form(...),
    description: str = Form(None),
    date: str = Form(...), # format YYYY-MM-DD
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(security.require_admin)
):
    try:
        dt = datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido")
        
    ev = models.CalendarEvent(
        title=title,
        description=description,
        day=dt.day,
        month=dt.month,
        year=dt.year
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return {"message": "Evento agregado", "event": ev}

@app.delete("/api/rrhh/calendar_events/{event_id}")
async def delete_calendar_event(
    event_id: int,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(security.require_admin)
):
    ev = db.query(models.CalendarEvent).filter(models.CalendarEvent.id == event_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    db.delete(ev)
    db.commit()
    return {"message": "Evento eliminado"}

@app.get("/api/rrhh/calendar_events")
async def get_calendar_events_admin(
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(security.require_admin)
):
    # Get future events or all events
    today = datetime.now()
    events = db.query(models.CalendarEvent).order_by(
        models.CalendarEvent.year.desc(),
        models.CalendarEvent.month.desc(),
        models.CalendarEvent.day.desc()
    ).limit(50).all()
    return events
"""

if "/api/rrhh/calendar_events" not in content:
    target = 'if __name__ == "__main__":'
    if target in content:
        content = content.replace(target, new_endpoints + "\n" + target)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print("Success: Admin calendar endpoints added to main.py")
    else:
        print("Error: Could not find target in main.py")
else:
    print("Endpoint already exists.")
