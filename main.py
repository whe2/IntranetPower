import os
import shutil
import io
import pandas as pd
from typing import List, Optional
from datetime import datetime
from dotenv import load_dotenv

from fastapi import FastAPI, Depends, HTTPException, status, Request, Form, File, UploadFile, Response, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from database import engine, get_db, Base
import models
import security
import email_util

load_dotenv()

# Ensure required directories exist
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "static/uploads")
DOCS_DIR = "static/docs"
IMG_DIR = "static/img"

for d in [UPLOAD_DIR, DOCS_DIR, IMG_DIR]:
    os.makedirs(d, exist_ok=True)

# Create sample doc files if missing
sample_docs = ["manual_empleado_2026.pdf", "planilla_vacaciones.pdf", "app_helpdesk.pdf", "plantilla_informe.docx"]
for doc_name in sample_docs:
    doc_path = os.path.join(DOCS_DIR, doc_name)
    if not os.path.exists(doc_path):
        with open(doc_path, "wb") as f:
            f.write(f"Contenido demo para {doc_name} en la Intranet Corporativa.".encode("utf-8"))

app = FastAPI(
    title="Intranet Platform API",
    description="Sistema de Intranet Corporativa con PostgreSQL y Autenticación JWT Robusta",
    version="1.0.0"
)

# Security Headers & CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

# Mount Static Files and Templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Pydantic Schemas
class FeedbackCreate(BaseModel):
    content: str

class ChatMessageCreate(BaseModel):
    message: str

class KpiItem(BaseModel):
    title: str
    value: str
    trend: str = "up"

class KpiListUpdate(BaseModel):
    metrics: List[KpiItem]

class CalendarEventCreate(BaseModel):
    day: int
    title: str
    description: Optional[str] = None

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, email: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[email] = websocket

    def disconnect(self, email: str):
        if email in self.active_connections:
            del self.active_connections[email]

    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            try:
                await connection.send_json(message)
            except:
                pass
                
    async def send_personal_message(self, message: dict, email: str):
        if email in self.active_connections:
            try:
                await self.active_connections[email].send_json(message)
            except:
                pass

manager = ConnectionManager()

# ==========================================
# RUTAS DE AUTENTICACIÓN
# ==========================================
@app.post("/api/auth/login")
async def login_for_access_token(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    client_ip = request.client.host if request.client else "unknown"

    # Rate limiting check
    if security.is_rate_limited(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos fallidos. Tu IP está temporalmente bloqueada por 5 minutos.",
        )

    user = db.query(models.User).filter(models.User.username == form_data.username.strip()).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        security.record_failed_attempt(client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo electrónico o contraseña incorrectos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Success: reset rate limit attempts for this IP
    security.clear_failed_attempts(client_ip)

    access_token = security.create_access_token(data={"sub": user.username, "role": user.role})

    # Set HTTP-Only Secure Cookie
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age= security.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax"
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "permissions": user.permissions or "",
            "avatar_url": user.avatar_url
        }
    }

@app.post("/api/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Sesión cerrada correctamente."}

@app.get("/api/auth/me")
async def get_me(current_user: models.User = Depends(security.get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "permissions": current_user.permissions or "",
        "avatar_url": current_user.avatar_url
    }

@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request, db: Session = Depends(get_db)):
    token = security.get_token_from_request(request)
    if not token:
        return RedirectResponse(url="/login")
    try:
        username = security._decode_token(token)
        current_user = db.query(models.User).filter(models.User.username == username).first()
        if not current_user:
            return RedirectResponse(url="/login")
    except:
        return RedirectResponse(url="/login")

    all_users = db.query(models.User).filter(models.User.is_active == True).all()
    employees = db.query(models.Employee).all()
    emp_map = {emp.name: emp.department for emp in employees}
    
    departments = {}
    for u in all_users:
        dept = emp_map.get(u.full_name, "General")
        if dept not in departments:
            departments[dept] = []
        departments[dept].append(u)

    return templates.TemplateResponse(request, "chat.html", {
        "request": request,
        "user": current_user,
        "departments": departments
    })

# ==========================================
# RUTAS DE INTRANET GENERAL (USUARIOS)
# ==========================================
@app.get("/api/intranet/dashboard")
async def get_dashboard_data(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    hero = db.query(models.Announcement).filter(models.Announcement.is_active == True).first()
    resources = db.query(models.Resource).order_by(models.Resource.id.desc()).all()
    employees = db.query(models.Employee).all()
    kpis = db.query(models.KpiMetric).all()
    calendar_events = db.query(models.CalendarEvent).all()

    # Encuentra el próximo cumpleaños
    all_emps_with_bday = db.query(models.Employee).filter(models.Employee.birthday_date != None, models.Employee.birthday_date != "").all()
    closest_emp = None
    if all_emps_with_bday:
        today = datetime.now().date()
        
        def get_next_bday(emp):
            try:
                # El HTML envia YYYY-MM-DD
                bday = datetime.strptime(emp.birthday_date, '%Y-%m-%d').date()
                this_year_bday = bday.replace(year=today.year)
                if this_year_bday < today:
                    this_year_bday = this_year_bday.replace(year=today.year + 1)
                return this_year_bday
            except:
                return datetime(9999, 12, 31).date()

        sorted_emps = sorted(all_emps_with_bday, key=get_next_bday)
        closest_emp = sorted_emps[0]
        
        # Formatear la fecha para que se vea bonita (ej. 15 de Octubre)
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        try:
            bday_dt = datetime.strptime(closest_emp.birthday_date, '%Y-%m-%d').date()
            closest_emp.birthday_date = f"{bday_dt.day} de {meses[bday_dt.month - 1]}"
        except:
            pass
            
    birthday_emp = closest_emp

    return {
        "user": {
            "full_name": current_user.full_name,
            "username": current_user.username,
            "email": current_user.email,
            "role": current_user.role,
            "permissions": current_user.permissions or "",
            "avatar_url": current_user.avatar_url
        },
        "hero": hero,
        "resources": resources,
        "employees": employees,
        "kpis": kpis,
        "calendar_events": calendar_events,
        "birthday_employee": birthday_emp
    }

@app.post("/api/feedback")
async def create_feedback(
    data: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    fb = models.Feedback(user_email=current_user.email, content=data.content)
    db.add(fb)
    db.commit()
    return {"message": "Feedback guardado exitosamente."}

import json

@app.get("/api/chat")
async def get_chat_messages(
    channel: str = "#General",
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    messages = db.query(models.ChatMessage).filter(models.ChatMessage.channel == channel).order_by(models.ChatMessage.id.asc()).limit(50).all()
    return messages

@app.websocket("/api/ws/chat")
async def websocket_chat(websocket: WebSocket, db: Session = Depends(get_db)):
    token = websocket.cookies.get("access_token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    if token.startswith("Bearer "):
        token = token[len("Bearer "):]
    
    try:
        username = security._decode_token(token)
        user = db.query(models.User).filter(models.User.username == username).first()
        if not user:
            raise Exception()
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(user.email, websocket)
    try:
        while True:
            data_str = await websocket.receive_text()
            try:
                data = json.loads(data_str)
            except:
                # Fallback para mensajes de texto plano del chat antiguo
                data = {"message": data_str, "recipient_email": None}
                
            recipient_email = data.get("recipient_email")
            message_text = data.get("message")
            
            if recipient_email:
                emails = sorted([user.email, recipient_email])
                channel = f"private_{emails[0]}_{emails[1]}"
            else:
                channel = "#General"

            # Save to db
            msg = models.ChatMessage(
                user_email=user.email,
                user_name=user.full_name,
                channel=channel,
                message=message_text
            )
            db.add(msg)
            db.commit()
            
            payload = {
                "user_name": user.full_name,
                "user_email": user.email,
                "message": message_text,
                "channel": channel
            }
            
            # Broadcast o personal
            if recipient_email:
                await manager.send_personal_message(payload, recipient_email)
                # Opcional: enviarlo a ti mismo (si tienes varias pestañas)
                if recipient_email != user.email:
                    await manager.send_personal_message(payload, user.email)
            else:
                await manager.broadcast(payload)
    except WebSocketDisconnect:
        manager.disconnect(user.email)

# ==========================================
# RUTAS DE GESTIÓN DE RRHH / ADMIN
# ==========================================
@app.post("/api/rrhh/hero")
async def update_hero_banner(
    title: Optional[str] = Form(None),
    image_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(security.require_admin)
):
    hero = db.query(models.Announcement).first()
    if not hero:
        hero = models.Announcement(title="Bienvenido a la Intranet")
        db.add(hero)

    if title:
        hero.title = title

    if image_file and image_file.filename:
        filename = f"hero_{int(datetime.utcnow().timestamp())}_{image_file.filename}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(image_file.file, buffer)
        hero.image_url = f"/{UPLOAD_DIR}/{filename}"

    db.commit()
    db.refresh(hero)
    return {"message": "Anuncio principal actualizado.", "hero": hero}

@app.get("/api/rrhh/resources")
async def list_resources(
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(security.require_admin)
):
    return db.query(models.Resource).order_by(models.Resource.id.desc()).all()

@app.post("/api/rrhh/resources")
async def upload_resource(
    title: str = Form(...),
    category: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(security.require_admin)
):
    filename = f"doc_{int(datetime.utcnow().timestamp())}_{file.filename}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_url = f"/{UPLOAD_DIR}/{filename}"
    res_obj = models.Resource(
        title=title,
        category=category,
        file_path=file_url,
        file_type=file.filename.split(".")[-1]
    )
    db.add(res_obj)
    db.commit()
    db.refresh(res_obj)
    return {"message": "Recurso publicado con éxito.", "resource": res_obj}

@app.delete("/api/rrhh/resources/{resource_id}")
async def delete_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(security.require_admin)
):
    res_obj = db.query(models.Resource).filter(models.Resource.id == resource_id).first()
    if not res_obj:
        raise HTTPException(status_code=404, detail="Recurso no encontrado")
    db.delete(res_obj)
    db.commit()
    return {"message": "Recurso eliminado."}

@app.get("/api/rrhh/departments")
async def get_departments(
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(security.require_admin)
):
    return db.query(models.Department).order_by(models.Department.name).all()

@app.post("/api/rrhh/departments")
async def add_department(
    name: str = Form(...),
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(security.require_admin)
):
    dep = db.query(models.Department).filter(models.Department.name == name).first()
    if dep:
        raise HTTPException(status_code=400, detail="El departamento ya existe.")
    
    new_dep = models.Department(name=name)
    db.add(new_dep)
    db.commit()
    db.refresh(new_dep)
    return {"message": "Departamento creado con éxito.", "department": new_dep}

@app.post("/api/rrhh/employees")
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

    return {"message": "Empleado actualizado exitosamente.", "employee": emp}

@app.post("/api/rrhh/kpis")
async def update_kpis(
    data: KpiListUpdate,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(security.require_admin)
):
    # Clear and replace or update
    db.query(models.KpiMetric).delete()
    for item in data.metrics:
        db.add(models.KpiMetric(title=item.title, value=item.value, trend=item.trend))
    db.commit()
    return {"message": "Métricas KPI actualizadas."}


@app.post("/api/rrhh/calendar")
async def add_calendar_event(
    data: CalendarEventCreate,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(security.require_admin)
):
    evt = models.CalendarEvent(day=data.day, title=data.title, description=data.description)
    db.add(evt)
    db.commit()
    return {"message": "Evento agregado al calendario."}

@app.get("/api/rrhh/users")
async def list_users_permissions(
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(security.require_admin)
):
    users = db.query(models.User).order_by(models.User.full_name).all()
    return [{"id": u.id, "full_name": u.full_name, "email": u.email, "role": u.role, "permissions": u.permissions or ""} for u in users]

@app.post("/api/rrhh/users/{user_id}/permissions")
async def update_user_permissions(
    user_id: int,
    permissions: str = Form(""),
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(security.require_admin)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user.permissions = permissions
    db.commit()
    return {"message": "Permisos actualizados correctamente"}

@app.get("/api/popup")
async def get_popup_notification(
    db: Session = Depends(get_db)
):
    popup = db.query(models.PopupNotification).order_by(models.PopupNotification.id.desc()).first()
    if popup and popup.is_active:
        return {"message": popup.message}
    return {"message": ""}

@app.post("/api/rrhh/popup")
async def update_popup_notification(
    message: str = Form(""),
    is_active: str = Form("true"),
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(security.require_admin)
):
    is_act = is_active.lower() == "true"
    popup = db.query(models.PopupNotification).first()
    if not popup:
        popup = models.PopupNotification(message=message, is_active=is_act)
        db.add(popup)
    else:
        popup.message = message
        popup.is_active = is_act
    db.commit()
    return {"status": "success", "message": "Pop-up actualizado."}

# ==========================================
# RUTAS DE PLANTILLAS VISTA HTML
# ==========================================
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    embed = request.query_params.get("embed") == "1"
    return templates.TemplateResponse(request, "login.html", {"embed": embed})

@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request, db: Session = Depends(get_db)):
    token = security.get_token_from_request(request)
    if not token:
        return RedirectResponse(url="/login")
    try:
        user = security.get_current_user(request, db)
        embed = request.query_params.get("embed") == "1"
        return templates.TemplateResponse(request, "intranet.html", {"user": user, "embed": embed})
    except HTTPException:
        return RedirectResponse(url="/login")

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, db: Session = Depends(get_db)):
    token = security.get_token_from_request(request)
    if not token:
        return RedirectResponse(url="/login")
    try:
        user = security.get_current_user(request, db)
        if user.role not in ["admin", "rrhh"] and "cargar_datos_usuarios" not in (user.permissions or ""):
            return RedirectResponse(url="/")
        
        employees = db.query(models.Employee).all()
        departments = db.query(models.Department).all()
        
        return templates.TemplateResponse(request, "rrhh.html", {
            "user": user,
            "employees": employees,
            "departments": departments
        })
    except HTTPException:
        return RedirectResponse(url="/login")

@app.get("/integracion", response_class=HTMLResponse)
async def integracion_page(request: Request, db: Session = Depends(get_db)):
    token = security.get_token_from_request(request)
    if not token:
        return RedirectResponse(url="/login")
    try:
        user = security.get_current_user(request, db)
        if user.role not in ["admin", "integracion", "rrhh"] and "ver_integracion" not in (user.permissions or ""):
            return RedirectResponse(url="/")
        embed = request.query_params.get("embed") == "1"
        return templates.TemplateResponse(request, "integracion.html", {"user": user, "embed": embed})
    except HTTPException:
        return RedirectResponse(url="/login")

@app.get("/helpdesk", response_class=HTMLResponse)
async def helpdesk_page(request: Request, db: Session = Depends(get_db)):
    token = security.get_token_from_request(request)
    if not token:
        return RedirectResponse(url="/login")
    try:
        user = security.get_current_user(request, db)
        if user.role not in ["admin"] and "ver_helpdesk" not in (user.permissions or ""):
            return RedirectResponse(url="/")
        return templates.TemplateResponse(request, "helpdesk.html", {"user": user})
    except HTTPException:
        return RedirectResponse(url="/login")

def safe_date_str(val):
    if pd.isna(val) or val == "":
        return ""
    if isinstance(val, datetime):
        return val.strftime("%d/%m/%Y")
    return str(val).split(" ")[0]

import urllib.request
import urllib.parse
import json
import time

def fetch_powerlink_data():
    login_url = "https://powerlink.rubpi.com/api/login"
    creds = {"username": "api_exp", "password": "-?J+\\FcmKT2zWl5A28=~"}
    data = json.dumps(creds).encode('utf-8')

    req = urllib.request.Request(login_url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode())
            api_token = res_data.get('token') or res_data.get('access_token')
    except Exception as e:
        raise Exception(f"Error en login API: {str(e)}")

    if not api_token:
        raise Exception("No se pudo obtener token de la API")

    export_url = "https://powerlink.rubpi.com/api/exports/users"
    req2 = urllib.request.Request(export_url, headers={'Authorization': f'Bearer {api_token}', 'Content-Type': 'application/json', 'Accept': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req2) as response:
            res2_data = json.loads(response.read().decode())
            task_id = res2_data.get('task_id') or res2_data.get('id')
    except Exception as e:
        raise Exception(f"Error al iniciar exportación: {str(e)}")

    if not task_id:
        raise Exception("No se obtuvo task_id")

    get_url = f"https://powerlink.rubpi.com/api/exports/users/{task_id}"
    
    for i in range(20): # try for 60 seconds
        time.sleep(3)
        req3 = urllib.request.Request(get_url, headers={'Authorization': f'Bearer {api_token}'}, method='GET')
        try:
            with urllib.request.urlopen(req3) as response:
                res3_data = json.loads(response.read().decode())
                return res3_data
        except urllib.error.HTTPError as e:
            if e.code == 400:
                continue
            raise Exception("Error de API: " + str(e.code))
        except Exception as e:
            raise Exception(f"Error al consultar tarea: {str(e)}")

    raise Exception("Tiempo de espera agotado para la tarea")

@app.get("/api/integracion/api_users")
def get_api_users(request: Request, db: Session = Depends(get_db)):
    token = security.get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="No autorizado")
    
    try:
        data = fetch_powerlink_data()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/integracion/guardar_snapshot")
def guardar_snapshot(request: Request, db: Session = Depends(get_db)):
    token = security.get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="No autorizado")
    
    try:
        data = fetch_powerlink_data()
        snapshot_path = os.path.join(UPLOAD_DIR, "last_snapshot.json")
        with open(snapshot_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
            
        current_time = datetime.now().strftime("%d/%m/%Y a las %I:%M %p")
        return {"message": "Registro anterior guardado exitosamente.", "time": current_time}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/integracion/procesar_api")
async def procesar_auditoria_api(
    request: Request,
    db: Session = Depends(get_db),
    fileOld: Optional[UploadFile] = File(None),
    fechaCorte: str = Form(...),
    fechaInstalaciones: str = Form(...)
):
    token = security.get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="No autorizado")
        
    try:
        data_new = fetch_powerlink_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo datos actuales: {str(e)}")
        
    old_dict = {}
    if fileOld and fileOld.filename:
        # Modo: Comparar con Excel Subido
        content_old = await fileOld.read()
        df_old = pd.read_excel(io.BytesIO(content_old))
        df_old = df_old.fillna("")
        for _, row in df_old.iterrows():
            sid = str(row.get('ID Servicio', '')).strip()
            if sid:
                old_dict[sid] = {
                    'ID Servicio': sid,
                    'Plan': row.get('Plan', ''),
                    'Estado servicio': row.get('Estado servicio', ''),
                    'Costo del plan': row.get('Costo del plan', 0)
                }
    else:
        # Modo: Comparar con Snapshot Local
        snapshot_path = os.path.join(UPLOAD_DIR, "last_snapshot.json")
        if not os.path.exists(snapshot_path):
            raise HTTPException(status_code=400, detail="No existe un registro anterior. Por favor, haz clic en 'Guardar Registro Actual (Anterior)' antes de comparar, o sube un Excel.")
            
        try:
            with open(snapshot_path, "r", encoding="utf-8") as f:
                data_old = json.load(f)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error leyendo el registro anterior: {str(e)}")
            
        list_old = data_old.get("data", [])
        for item in list_old:
            sid = str(item.get('id_servicio', '')).strip()
            if sid:
                old_dict[sid] = {
                    'ID Servicio': sid,
                    'Plan': item.get('plan', ''),
                    'Estado servicio': item.get('service_status', ''),
                    'Costo del plan': item.get('amount', 0)
                }

    list_new = data_new.get("data", [])
    
    def map_to_excel_format(item):
        return {
            'ID Servicio': item.get('id_servicio', ''),
            'Cédula': f"{item.get('doc_type', '')}-{item.get('doc', '')}",
            'Nombres': item.get('name', ''),
            'Plan': item.get('plan', ''),
            'Tipo de servicio': item.get('service_type', ''),
            'Costo del plan': item.get('amount', 0),
            'Estado servicio': item.get('service_status', ''),
            'Saldo actual': item.get('balance', 0),
            'Fecha última cambio de estado': item.get('last_status_change_date', ''),
            'Plan actual desde': item.get('current_plan_since', ''),
            'Fecha de instalación': item.get('creation_date', ''),
            'Teléfono 1': item.get('phone', ''),
            'Urbanismo': item.get('urban', '')
        }

    try:
        corte_dt = datetime.strptime(fechaCorte, "%Y-%m-%d")
    except:
        corte_dt = datetime.min
        
    try:
        inst_dt = datetime.strptime(fechaInstalaciones, "%Y-%m-%d")
        inst_str = inst_dt.strftime("%d/%m/%Y")
    except:
        inst_str = ""

    today_str = datetime.now().strftime("%d/%m/%Y")

    totalActivos = 0
    totalSuspendidosFecha = 0
    totalExoneradosEmp = 0
    totalExoneradosReg = 0
    
    datosInstalaciones = []
    datosInstalacionesProceso = []
    datosCambiosPlan = []
    datosSeguimiento = []
    datosEstatus = []
    datosDeudores = []
    
    for item in list_new:
        row = map_to_excel_format(item)
        sid = str(row['ID Servicio']).strip()
        if not sid:
            continue
            
        planNew = str(row['Plan']).strip()
        tipoServicioNew = str(row['Tipo de servicio']).strip().upper()
        
        try:
            costoDelPlanNew = float(row['Costo del plan'])
        except:
            costoDelPlanNew = 0.0
            
        if planNew.upper() == 'TV' or planNew.upper() == 'IPTV' or tipoServicioNew == 'IPTV':
            continue
            
        estadoServicioNew = str(row['Estado servicio']).strip().upper()
        
        try:
            saldoActual = float(row['Saldo actual'])
        except:
            saldoActual = 0.0
            
        raw_estado = row['Fecha última cambio de estado']
        raw_plan = row['Plan actual desde']
        raw_inst = row['Fecha de instalación']
        
        fechaEstadoFormat = safe_date_str(raw_estado)
        fechaPlanDesdeFormat = safe_date_str(raw_plan)
        fechaInstalacionFormat = safe_date_str(raw_inst)
        
        estado_dt = datetime.min
        if raw_estado:
            date_only = str(raw_estado).split("T")[0]
            try:
                estado_dt = datetime.strptime(date_only, "%Y-%m-%d")
                fechaEstadoFormat = estado_dt.strftime("%d/%m/%Y")
            except:
                pass

        if raw_inst:
            date_only = str(raw_inst).split("T")[0]
            try:
                inst_p = datetime.strptime(date_only, "%Y-%m-%d")
                fechaInstalacionFormat = inst_p.strftime("%d/%m/%Y")
            except:
                pass
                 
        if raw_plan:
             date_only = str(raw_plan).split("T")[0]
             try:
                 plan_p = datetime.strptime(date_only, "%Y-%m-%d")
                 fechaPlanDesdeFormat = plan_p.strftime("%d/%m/%Y")
             except:
                 pass
                
        if estadoServicioNew == 'ACTIVO':
            totalActivos += 1
        elif estadoServicioNew == 'SUSPENDIDO':
            if estado_dt >= corte_dt:
                totalSuspendidosFecha += 1
        elif estadoServicioNew == 'EXONERADO':
            if planNew.lower().startswith('(emp)') or planNew.lower().startswith('emp'):
                totalExoneradosEmp += 1
            else:
                totalExoneradosReg += 1
                
        is_missing_in_old = (sid not in old_dict)
        is_exact_date_match = (fechaInstalacionFormat == inst_str)
        
        if estadoServicioNew == 'ACTIVO' and (is_exact_date_match or is_missing_in_old):
            if planNew.upper().startswith("3 MESES BENEFICIO"):
                datosInstalaciones.append({
                    'ID Servicio': sid,
                    'Cédula': row['Cédula'],
                    'Nombres': row['Nombres'],
                    'Estado servicio': row['Estado servicio'],
                    'Plan': row['Plan'],
                    'Costo del plan': row['Costo del plan'],
                    'Fecha de instalación': fechaInstalacionFormat,
                    'Urbanismo': row['Urbanismo'],
                    'Saldo Actual': saldoActual
                })
                
        if estadoServicioNew == 'ACTIVO' and fechaInstalacionFormat == today_str:
            datosInstalacionesProceso.append({
                'ID Servicio': sid,
                'Cédula': row['Cédula'],
                'Nombres': row['Nombres'],
                'Estado servicio': row['Estado servicio'],
                'Plan': row['Plan'],
                'Costo del plan': row['Costo del plan'],
                'Fecha de instalación': fechaInstalacionFormat,
                'Urbanismo': row['Urbanismo'],
                'Saldo Actual': saldoActual
            })
                
        if estadoServicioNew == 'ACTIVO' and saldoActual < 0:
            datosDeudores.append({
                'ID Servicio': sid,
                'Cédula': row['Cédula'],
                'Nombres': row['Nombres'],
                'Estado servicio': row['Estado servicio'],
                'Saldo Actual (Deuda)': saldoActual,
                'Plan': row['Plan'],
                'Costo del plan': row['Costo del plan'],
                'Fecha Último Cambio Estado': fechaEstadoFormat,
                'Teléfono 1': row['Teléfono 1']
            })
            
        row_old = old_dict.get(sid)
        if row_old is not None:
            planOld = str(row_old['Plan']).strip()
            estatusOld = str(row_old['Estado servicio']).strip().upper()
            estatusNew = estadoServicioNew
            try:
                costoOld = float(row_old['Costo del plan'])
            except:
                costoOld = 0.0
                
            billingAyer = costoOld if estatusOld == 'ACTIVO' else 0.0
            billingHoy = costoDelPlanNew if estatusNew == 'ACTIVO' else 0.0
            variacionNeta = billingHoy - billingAyer
            
            if planOld != planNew:
                datosCambiosPlan.append({
                    'ID Servicio': sid,
                    'Cédula': row['Cédula'],
                    'Nombres': row['Nombres'],
                    'Plan Anterior': planOld,
                    'Plan Nuevo': planNew,
                    'Costo Anterior': costoOld,
                    'Costo Nuevo': costoDelPlanNew,
                    'Variación de Costo': variacionNeta,
                    'Estado Actual': row['Estado servicio'],
                    'Estado Anterior': estatusOld,
                    'Estado Nuevo': estatusNew,
                    'Fecha Plan Actual Desde': fechaPlanDesdeFormat 
                })
                
            if planOld != planNew or estatusOld != estatusNew:
                datosSeguimiento.append({
                    'ID Servicio': sid,
                    'Cédula': row['Cédula'],
                    'Nombres': row['Nombres'],
                    'Plan Anterior': planOld,
                    'Plan Nuevo': planNew,
                    'Costo Anterior': costoOld,
                    'Costo Nuevo': costoDelPlanNew,
                    'Variación de Costo': variacionNeta,
                    'Estado Anterior': estatusOld,
                    'Estado Nuevo': estatusNew,
                    'Fecha Último Cambio Estado': fechaEstadoFormat,
                    'Fecha Plan Actual Desde': fechaPlanDesdeFormat
                })
                
            if estatusOld != estatusNew:
                datosEstatus.append({
                    'ID Servicio': sid,
                    'Cédula': row['Cédula'],
                    'Nombres': row['Nombres'],
                    'Plan Actual': planNew,
                    'Costo Anterior': costoOld,
                    'Costo Nuevo': costoDelPlanNew,
                    'Variación de Costo': variacionNeta,
                    'Estado Anterior': estatusOld,
                    'Estado Nuevo': estatusNew,
                    'Fecha Último Cambio Estado': fechaEstadoFormat
                })

    def _sort_by_nombres(x): return x.get('Nombres', '')
    
    datosInstalaciones.sort(key=_sort_by_nombres)
    datosInstalacionesProceso.sort(key=_sort_by_nombres)
    datosCambiosPlan.sort(key=_sort_by_nombres)
    datosSeguimiento.sort(key=_sort_by_nombres)
    datosEstatus.sort(key=_sort_by_nombres)
    datosDeudores.sort(key=_sort_by_nombres)

    resumen_list = [
        {"Indicador": "Activos Totales", "Valor": totalActivos},
        {"Indicador": f"Suspendidos (desde {fechaCorte})", "Valor": totalSuspendidosFecha},
        {"Indicador": "Exonerados (Empleados)", "Valor": totalExoneradosEmp},
        {"Indicador": "Exonerados (Regulares)", "Valor": totalExoneradosReg}
    ]

    return {
        "totales": {
            "activos": totalActivos,
            "suspendidos": totalSuspendidosFecha,
            "exonEmp": totalExoneradosEmp,
            "exonReg": totalExoneradosReg
        },
        "resumen": resumen_list,
        "instalaciones": datosInstalaciones,
        "instalacionesProceso": datosInstalacionesProceso,
        "cambiosPlan": datosCambiosPlan,
        "seguimiento": datosSeguimiento,
        "estatus": datosEstatus,
        "deudores": datosDeudores
    }

@app.get("/api/metricas/crecimiento")
def get_metricas_crecimiento(request: Request, db: Session = Depends(get_db)):
    token = security.get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="No autorizado")
        
    snapshot_path = os.path.join(UPLOAD_DIR, "last_snapshot.json")
    if not os.path.exists(snapshot_path):
        return {"activos_power": 0}
        
    try:
        with open(snapshot_path, "r", encoding="utf-8") as f:
            data_old = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error leyendo snapshot: {str(e)}")
        
    list_old = data_old.get("data", [])
    activos_power = 0
    activos_iptv = 0
    
    for item in list_old:
        status = str(item.get('service_status', '')).strip().upper()
        plan = str(item.get('plan', '')).strip().upper()
        service_type = str(item.get('service_type', '')).strip().upper()
        
        if status == 'ACTIVO':
            if plan == 'TV' or plan == 'IPTV' or service_type == 'IPTV':
                activos_iptv += 1
            else:
                activos_power += 1
            
    return {
        "activos_power": activos_power,
        "activos_iptv": activos_iptv
    }


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


# ==========================================
# DIRECTORIO TELEFONICO
# ==========================================
@app.get("/directorio", response_class=HTMLResponse)
async def view_directorio(request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    employees = db.query(models.Employee).all()
    return templates.TemplateResponse(request, "directorio.html", {"request": request, "user": current_user, "employees": employees})

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
