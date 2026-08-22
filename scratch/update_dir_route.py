import re

filepath = r"c:\Users\wgallardo\Documents\Proyectos gravity\intranet\main.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

target = """@app.get("/directorio", response_class=HTMLResponse)
async def view_directorio(request: Request, current_user: models.User = Depends(security.get_current_user)):
    return templates.TemplateResponse("directorio.html", {"request": request, "user": current_user})"""

replacement = """@app.get("/directorio", response_class=HTMLResponse)
async def view_directorio(request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    employees = db.query(models.Employee).all()
    return templates.TemplateResponse("directorio.html", {"request": request, "user": current_user, "employees": employees})"""

if target in content:
    content = content.replace(target, replacement)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated main.py /directorio endpoint")
else:
    print("Target not found in main.py")
