import os
import shutil
import io
import pandas as pd
from typing import List, Optional
from datetime import datetime
from dotenv import load_dotenv

from fastapi import FastAPI, Depends, HTTPException, status, Request, Form, File, UploadFile, Response
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

    user = db.query(models.User).filter(models.User.email == form_data.username.strip()).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        security.record_failed_attempt(client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo electrónico o contraseña incorrectos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Success: reset rate limit attempts for this IP
    security.clear_failed_attempts(client_ip)

    access_token = security.create_access_token(data={"sub": user.email, "role": user.role})

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
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
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
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "avatar_url": current_user.avatar_url
    }

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

    # Find birthday employee (e.g. Carlos Mendoza or latest)
    birthday_emp = db.query(models.Employee).filter(models.Employee.birthday_date != None).first()

    return {
        "user": {
            "full_name": current_user.full_name,
            "email": current_user.email,
            "role": current_user.role,
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

@app.get("/api/chat")
async def get_chat_messages(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    messages = db.query(models.ChatMessage).order_by(models.ChatMessage.id.asc()).limit(50).all()
    return messages

@app.post("/api/chat")
async def post_chat_message(
    data: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    msg = models.ChatMessage(
        user_email=current_user.email,
        user_name=current_user.full_name,
        channel="#General",
        message=data.message
    )
    db.add(msg)
    db.commit()
    return {"message": "Mensaje enviado."}

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

@app.post("/api/rrhh/employees")
async def add_employee(
    name: str = Form(...),
    position: str = Form(...),
    photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(security.require_admin)
):
    photo_url = "https://ngfihmioixtfnrmlrlam.supabase.co/storage/v1/object/public/power/Gemini_Generated_Image_glf24lglf24lglf2.png"
    if photo and photo.filename:
        filename = f"emp_{int(datetime.utcnow().timestamp())}_{photo.filename}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
        photo_url = f"/{UPLOAD_DIR}/{filename}"

    emp = models.Employee(name=name, position=position, photo_url=photo_url)
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return {"message": "Empleado agregado.", "employee": emp}

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

@app.post("/api/rrhh/birthday")
async def update_birthday(
    name: str = Form(...),
    birthday_date: str = Form(...),
    photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(security.require_admin)
):
    emp = db.query(models.Employee).filter(models.Employee.name == name).first()
    photo_url = None
    if photo and photo.filename:
        filename = f"bday_{int(datetime.utcnow().timestamp())}_{photo.filename}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
        photo_url = f"/{UPLOAD_DIR}/{filename}"

    if not emp:
        emp = models.Employee(
            name=name,
            position="Empleado",
            birthday_date=birthday_date,
            photo_url=photo_url or "https://ngfihmioixtfnrmlrlam.supabase.co/storage/v1/object/public/power/Gemini_Generated_Image_glf24lglf24lglf2.png"
        )
        db.add(emp)
    else:
        emp.birthday_date = birthday_date
        if photo_url:
            emp.photo_url = photo_url

    db.commit()
    return {"message": "Cumpleaños actualizado."}

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

# ==========================================
# RUTAS DE PLANTILLAS VISTA HTML
# ==========================================
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")

@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request, db: Session = Depends(get_db)):
    token = security.get_token_from_request(request)
    if not token:
        return RedirectResponse(url="/login")
    try:
        user = security.get_current_user(request, db)
        return templates.TemplateResponse(request, "intranet.html", {"user": user})
    except HTTPException:
        return RedirectResponse(url="/login")

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, db: Session = Depends(get_db)):
    token = security.get_token_from_request(request)
    if not token:
        return RedirectResponse(url="/login")
    try:
        user = security.get_current_user(request, db)
        if user.role not in ["admin", "rrhh"]:
            return RedirectResponse(url="/")
        return templates.TemplateResponse(request, "rrhh.html", {"user": user})
    except HTTPException:
        return RedirectResponse(url="/login")

@app.get("/integracion", response_class=HTMLResponse)
async def integracion_page(request: Request, db: Session = Depends(get_db)):
    token = security.get_token_from_request(request)
    if not token:
        return RedirectResponse(url="/login")
    try:
        user = security.get_current_user(request, db)
        if user.role not in ["admin", "integracion", "rrhh"]:
            return RedirectResponse(url="/")
        return templates.TemplateResponse(request, "integracion.html", {"user": user})
    except HTTPException:
        return RedirectResponse(url="/login")

def safe_date_str(val):
    if pd.isna(val) or val == "":
        return ""
    if isinstance(val, datetime):
        return val.strftime("%d/%m/%Y")
    return str(val).split(" ")[0]

@app.post("/api/integracion/procesar")
async def procesar_auditoria(
    request: Request,
    db: Session = Depends(get_db),
    fileOld: UploadFile = File(...),
    fileNew: UploadFile = File(...),
    fechaCorte: str = Form(...),
    fechaInstalaciones: str = Form(...)
):
    token = security.get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="No autorizado")
    
    content_old = await fileOld.read()
    content_new = await fileNew.read()
    
    df_old = pd.read_excel(io.BytesIO(content_old))
    df_new = pd.read_excel(io.BytesIO(content_new))
    
    df_old = df_old.fillna("")
    df_new = df_new.fillna("")
    
    try:
        corte_dt = datetime.strptime(fechaCorte, "%Y-%m-%d")
    except:
        corte_dt = datetime.min
        
    try:
        inst_dt = datetime.strptime(fechaInstalaciones, "%Y-%m-%d")
        inst_str = inst_dt.strftime("%d/%m/%Y")
    except:
        inst_str = ""

    old_dict = {}
    for _, row in df_old.iterrows():
        sid = str(row.get('ID Servicio', '')).strip()
        if sid:
            old_dict[sid] = row

    totalActivos = 0
    totalSuspendidosFecha = 0
    totalExoneradosEmp = 0
    totalExoneradosReg = 0
    
    datosInstalaciones = []
    datosCambiosPlan = []
    datosSeguimiento = []
    datosEstatus = []
    datosDeudores = []

    for _, row in df_new.iterrows():
        sid = str(row.get('ID Servicio', '')).strip()
        if not sid:
            continue
            
        planNew = str(row.get('Plan', '')).strip()
        tipoServicioNew = str(row.get('Tipo de servicio', '')).strip().upper()
        
        try:
            costoDelPlanNew = float(row.get('Costo del plan', 0))
        except:
            costoDelPlanNew = 0.0
            
        if planNew.upper() == 'TV' or planNew.upper() == 'IPTV' or tipoServicioNew == 'IPTV':
            continue
            
        estadoServicioNew = str(row.get('Estado servicio', '')).strip().upper()
        
        try:
            saldoActual = float(row.get('Saldo actual', 0))
        except:
            saldoActual = 0.0
            
        raw_estado = row.get('Fecha última cambio de estado', '')
        raw_plan = row.get('Plan actual desde', '')
        raw_inst = row.get('Fecha de instalación', '')
        
        fechaEstadoFormat = safe_date_str(raw_estado)
        fechaPlanDesdeFormat = safe_date_str(raw_plan)
        fechaInstalacionFormat = safe_date_str(raw_inst)
        
        estado_dt = datetime.min
        if fechaEstadoFormat:
            try:
                estado_dt = datetime.strptime(fechaEstadoFormat, "%d/%m/%Y")
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
                
        if estadoServicioNew == 'ACTIVO' and fechaInstalacionFormat == inst_str:
            if planNew.upper().startswith("3 MESES BENEFICIO"):
                datosInstalaciones.append({
                    'ID Servicio': sid,
                    'Cédula': row.get('Cédula', ''),
                    'Nombres': row.get('Nombres', ''),
                    'Estado servicio': row.get('Estado servicio', ''),
                    'Plan Instalado': row.get('Plan', ''),
                    'Costo del plan': row.get('Costo del plan', ''),
                    'Fecha de Instalación': fechaInstalacionFormat,
                    'Urbanismo': row.get('Urbanismo', '')
                })
                
        if estadoServicioNew == 'ACTIVO' and saldoActual < 0:
            datosDeudores.append({
                'ID Servicio': sid,
                'Cédula': row.get('Cédula', ''),
                'Nombres': row.get('Nombres', ''),
                'Estado servicio': row.get('Estado servicio', ''),
                'Saldo Actual (Deuda)': saldoActual,
                'Plan': row.get('Plan', ''),
                'Costo del plan': row.get('Costo del plan', ''),
                'Fecha Último Cambio Estado': fechaEstadoFormat,
                'Teléfono 1': row.get('Teléfono 1', '')
            })
            
        row_old = old_dict.get(sid)
        if row_old is not None:
            planOld = str(row_old.get('Plan', '')).strip()
            estatusOld = str(row_old.get('Estado servicio', '')).strip()
            estatusNew = str(row.get('Estado servicio', '')).strip()
            try:
                costoOld = float(row_old.get('Costo del plan', 0))
            except:
                costoOld = 0.0
                
            if planOld != planNew:
                datosCambiosPlan.append({
                    'ID Servicio': sid,
                    'Cédula': row.get('Cédula', ''),
                    'Nombres': row.get('Nombres', ''),
                    'Plan Anterior': row_old.get('Plan', ''),
                    'Plan Nuevo': row.get('Plan', ''),
                    'Costo Anterior': costoOld,
                    'Costo Nuevo': costoDelPlanNew,
                    'Estado Actual': row.get('Estado servicio', ''),
                    'Fecha Plan Actual Desde': fechaPlanDesdeFormat 
                })
                
            if planOld != planNew or estatusOld != estatusNew:
                datosSeguimiento.append({
                    'ID Servicio': sid,
                    'Cédula': row.get('Cédula', ''),
                    'Nombres': row.get('Nombres', ''),
                    'Plan Anterior': row_old.get('Plan', ''),
                    'Plan Nuevo': row.get('Plan', ''),
                    'Costo Anterior': costoOld,
                    'Costo Nuevo': costoDelPlanNew,
                    'Estado Anterior': row_old.get('Estado servicio', ''),
                    'Estado Nuevo': row.get('Estado servicio', ''),
                    'Fecha Último Cambio Estado': fechaEstadoFormat,
                    'Fecha Plan Actual Desde': fechaPlanDesdeFormat
                })
                
            if estatusOld != estatusNew:
                datosEstatus.append({
                    'ID Servicio': sid,
                    'Cédula': row.get('Cédula', ''),
                    'Nombres': row.get('Nombres', ''),
                    'Plan Actual': row.get('Plan', ''),
                    'Costo del Plan (Actual)': costoDelPlanNew,
                    'Estado Anterior': row_old.get('Estado servicio', ''),
                    'Estado Nuevo': row.get('Estado servicio', ''),
                    'Fecha Último Cambio Estado': fechaEstadoFormat
                })

    corte_str = f"{corte_dt.day:02d}/{corte_dt.month:02d}/{corte_dt.year}" if corte_dt != datetime.min else ""
    
    cuadroResumenFinal = [
        { "Métrica Operativa (Sin IPTV)": "Clientes Activos Totales", "Cantidad": totalActivos },
        { "Métrica Operativa (Sin IPTV)": f"Clientes Suspendidos (A partir del {corte_str})", "Cantidad": totalSuspendidosFecha },
        { "Métrica Operativa (Sin IPTV)": "Clientes Exonerados - Empleados [emp]", "Cantidad": totalExoneradosEmp },
        { "Métrica Operativa (Sin IPTV)": "Clientes Exonerados - Regulares", "Cantidad": totalExoneradosReg }
    ]

    return JSONResponse(content={
        "resumen": cuadroResumenFinal,
        "instalaciones": datosInstalaciones,
        "cambiosPlan": datosCambiosPlan,
        "seguimiento": datosSeguimiento,
        "estatus": datosEstatus,
        "deudores": datosDeudores,
        "totales": {
            "activos": totalActivos,
            "suspendidos": totalSuspendidosFecha,
            "exonEmp": totalExoneradosEmp,
            "exonReg": totalExoneradosReg
        }
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
