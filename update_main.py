import os

file_path = r"c:\Users\wgallardo\Documents\Proyectos gravity\intranet\main.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add import email_util
if 'import email_util' not in content:
    content = content.replace('import security', 'import security\nimport email_util')

# 2. Replace add_employee
old_add_employee_start = """@app.post("/api/rrhh/employees")
async def add_employee("""
old_add_employee_end = """    db.refresh(emp)
    return {"message": "Empleado y credenciales agregados.", "employee": emp}"""

import re
old_add_employee_block = re.search(r'@app\.post\("/api/rrhh/employees"\).*?return \{"message": "Empleado y credenciales agregados.", "employee": emp\}', content, re.DOTALL)

new_employee_endpoints = """@app.post("/api/rrhh/employees")
async def add_employee(
    name: str = Form(...),
    apellido: str = Form(...),
    position: str = Form(...),
    department: str = Form(None),
    cedula: str = Form(None),
    birthday_date: str = Form(None),
    email: str = Form(None),
    smtp_user: str = Form(None),
    smtp_pass: str = Form(None),
    photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(security.require_admin)
):
    if cedula:
        existing = db.query(models.Employee).filter(models.Employee.cedula == cedula).first()
        if existing:
            raise HTTPException(status_code=400, detail="Empleado ya se encuentra en sistema")

    if email:
        existing_emp = db.query(models.Employee).filter(models.Employee.email == email).first()
        if existing_emp:
            raise HTTPException(status_code=400, detail="El correo electrónico ya existe para otro empleado.")

    usuario = (name[0] + apellido).lower() if name and apellido else "usuario"
    base_username = usuario
    counter = 1
    while db.query(models.User).filter(models.User.username == usuario).first():
        usuario = f"{base_username}{counter}"
        counter += 1
        
    import random
    palabras = ['Power', 'Link', 'Gravity', 'System', 'Secure', 'Admin']
    password = random.choice(palabras) + random.choice(['*','#','$','&','@']) + str(random.randint(100,999))

    photo_url = "https://ngfihmioixtfnrmlrlam.supabase.co/storage/v1/object/public/power/WhatsApp_Image_2026-03-20_at_3.44.14_PM-removebg-preview.png"
    if photo and photo.filename:
        filename = f"emp_{int(datetime.utcnow().timestamp())}_{photo.filename}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
        photo_url = f"/{UPLOAD_DIR}/{filename}"

    emp = models.Employee(name=name, apellido=apellido, email=email, position=position, department=department or "General", 
cedula=cedula, birthday_date=birthday_date, photo_url=photo_url)
    db.add(emp)
    
    hashed_pw = security.get_password_hash(password)
    new_user = models.User(
        username=usuario,
        email=email or f"{usuario}@empresa.com",
        hashed_password=hashed_pw,
        full_name=f"{name} {apellido}",
        role="user",
        avatar_url=photo_url
    )
    db.add(new_user)
        
    db.commit()
    db.refresh(emp)
    
    # Send email
    if email and smtp_user and smtp_pass:
        email_util.send_welcome_email(email, name, usuario, password, smtp_user, smtp_pass, is_update=False)
        
    return {"message": "Empleado y credenciales agregados.", "employee": emp}

@app.put("/api/rrhh/employees/{emp_id}")
async def update_employee(
    emp_id: int,
    name: str = Form(...),
    apellido: str = Form(...),
    department: str = Form(None),
    cedula: str = Form(None),
    birthday_date: str = Form(None),
    email: str = Form(None),
    smtp_user: str = Form(None),
    smtp_pass: str = Form(None),
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(security.require_admin)
):
    emp = db.query(models.Employee).filter(models.Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
        
    # Validations for unique fields if they changed
    if cedula and cedula != emp.cedula:
        if db.query(models.Employee).filter(models.Employee.cedula == cedula).first():
            raise HTTPException(status_code=400, detail="Cédula ya está en uso")
            
    if email and email != emp.email:
        if db.query(models.Employee).filter(models.Employee.email == email).first():
            raise HTTPException(status_code=400, detail="Correo ya está en uso")

    emp.name = name
    emp.apellido = apellido
    emp.department = department or "General"
    emp.cedula = cedula
    emp.birthday_date = birthday_date
    emp.email = email
    
    db.commit()
    db.refresh(emp)
    
    if email and smtp_user and smtp_pass:
        email_util.send_welcome_email(email, name, "", "", smtp_user, smtp_pass, is_update=True)

    return {"message": "Empleado actualizado exitosamente.", "employee": emp}"""

if old_add_employee_block:
    content = content.replace(old_add_employee_block.group(0), new_employee_endpoints)
else:
    print("Could not find add_employee block!")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated main.py")
