import re

filepath = r"c:\Users\wgallardo\Documents\Proyectos gravity\intranet\main.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

new_endpoints = """
# ==========================================
# DIRECTORIO TELEFONICO
# ==========================================
@app.get("/directorio", response_class=HTMLResponse)
async def view_directorio(request: Request, current_user: models.User = Depends(security.get_current_user)):
    return templates.TemplateResponse("directorio.html", {"request": request, "user": current_user})

@app.get("/api/directorio/extensions")
async def get_extensions(db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    extensions = db.query(models.PhoneExtension).all()
    # Group by department
    data = {}
    for ext in extensions:
        if ext.department not in data:
            data[ext.department] = []
        data[ext.department].append({
            "id": ext.id,
            "name": ext.name,
            "extension": ext.extension,
            "is_group": ext.is_group
        })
    return data
"""

if "/directorio" not in content:
    target = 'if __name__ == "__main__":'
    if target in content:
        content = content.replace(target, new_endpoints + "\n" + target)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print("Success: Directory endpoints added to main.py")
    else:
        print("Error: Could not find target in main.py")
else:
    print("Endpoints already exist.")
