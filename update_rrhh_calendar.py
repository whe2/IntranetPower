import re

filepath = r"c:\Users\wgallardo\Documents\Proyectos gravity\intranet\templates\rrhh.html"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

target_html = """                <form onsubmit="addCalendarEvent(event)">
                    <div class="form-group">
                        <label>Día del Mes (Número)</label>
                        <input type="number" id="calDay" class="form-control" min="1" max="31" value="15" required>
                    </div>
                    <div class="form-group">
                        <label>Título del Evento</label>
                        <input type="text" id="calTitle" class="form-control" placeholder="Ej. Reunión General de Personal" required>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn-action" style="background:#ddd; color:#333;" onclick="closeModal('calModal')">Cancelar</button>
                        <button type="submit" class="btn-action btn-gold">Destacar Día en Calendario</button>
                    </div>
                </form>"""

new_html = """                <form onsubmit="addCalendarEvent(event)" id="calForm">
                    <div class="form-group">
                        <label>Fecha del Evento</label>
                        <input type="date" id="calDate" class="form-control" required>
                    </div>
                    <div class="form-group">
                        <label>Título del Evento</label>
                        <input type="text" id="calTitle" class="form-control" placeholder="Ej. Reunión General de Personal" required>
                    </div>
                    <div class="form-group">
                        <label>Descripción (Opcional)</label>
                        <textarea id="calDesc" class="form-control" rows="2" placeholder="Detalles de la actividad..."></textarea>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn-action" style="background:#ddd; color:#333;" onclick="closeModal('calModal')">Cancelar</button>
                        <button type="submit" class="btn-action btn-gold">Guardar Evento</button>
                    </div>
                </form>"""

if target_html in content:
    content = content.replace(target_html, new_html)

target_js = """        async function addCalendarEvent(e) {
            e.preventDefault();
            const day = document.getElementById('calDay').value;
            const title = document.getElementById('calTitle').value.trim();

            try {
                const res = await fetch('/api/rrhh/calendar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ day: parseInt(day), title: title })
                });
                if (res.ok) {
                    showToast('Evento registrado en calendario.');
                    closeModal('calModal');
                }
            } catch (e) { }
        }"""

new_js = """        async function addCalendarEvent(e) {
            e.preventDefault();
            const date = document.getElementById('calDate').value;
            const title = document.getElementById('calTitle').value.trim();
            const desc = document.getElementById('calDesc').value.trim();

            const formData = new FormData();
            formData.append('date', date);
            formData.append('title', title);
            if(desc) formData.append('description', desc);

            try {
                const res = await fetch('/api/rrhh/calendar_events', {
                    method: 'POST',
                    body: formData
                });
                if (res.ok) {
                    showToast('Evento registrado exitosamente.');
                    document.getElementById('calForm').reset();
                    closeModal('calModal');
                    loadCalendarEventsAdmin();
                } else {
                    showToast('Error al registrar el evento', 'error');
                }
            } catch (err) { showToast('Error de red', 'error'); }
        }

        async function loadCalendarEventsAdmin() {
            try {
                const res = await fetch('/api/rrhh/calendar_events');
                if (res.ok) {
                    const events = await res.json();
                    const container = document.getElementById('adminEventsList');
                    if(!container) return;
                    
                    container.innerHTML = '';
                    events.forEach(ev => {
                        const div = document.createElement('div');
                        div.style.padding = "8px 12px";
                        div.style.borderBottom = "1px solid #e2e8f0";
                        div.style.display = "flex";
                        div.style.justifyContent = "space-between";
                        div.style.alignItems = "center";
                        div.innerHTML = `
                            <div>
                                <strong style="font-size:13px; color:var(--texto-negro);">${ev.title}</strong>
                                <div style="font-size:11px; color:var(--texto-gris);"><i class="fa-regular fa-calendar"></i> ${ev.day}/${ev.month}/${ev.year}</div>
                            </div>
                            <button onclick="deleteCalendarEvent(${ev.id})" style="background:none; border:none; color:#ef4444; cursor:pointer;"><i class="fa-solid fa-trash"></i></button>
                        `;
                        container.appendChild(div);
                    });
                    if(events.length === 0) {
                        container.innerHTML = '<div style="padding:10px; text-align:center; font-size:12px; color:#94a3b8;">No hay eventos</div>';
                    }
                }
            } catch(e) {}
        }
        
        async function deleteCalendarEvent(id) {
            if(!confirm("¿Seguro que deseas eliminar este evento?")) return;
            try {
                const res = await fetch(`/api/rrhh/calendar_events/${id}`, { method: 'DELETE' });
                if(res.ok) {
                    showToast('Evento eliminado');
                    loadCalendarEventsAdmin();
                }
            } catch(e){}
        }"""

if target_js in content:
    content = content.replace(target_js, new_js)


target_cal_btn = """                <!-- CALENDARIO -->
                <div class="card">
                    <div class="section-title">📅 Marcar Evento en Calendario</div>
                    <button class="btn-action" style="width:100%; background-color:#334155;" onclick="openModal('calModal')">
                        <i class="fa-regular fa-calendar-plus"></i> Marcar Evento
                    </button>
                </div>"""
new_cal_btn = """                <!-- CALENDARIO -->
                <div class="card">
                    <div class="section-title">📅 Marcar Evento en Calendario</div>
                    <button class="btn-action" style="width:100%; background-color:#334155; margin-bottom:12px;" onclick="openModal('calModal')">
                        <i class="fa-regular fa-calendar-plus"></i> Marcar Evento
                    </button>
                    <div style="max-height: 180px; overflow-y: auto; border: 1px solid #e2e8f0; border-radius: 8px; background-color: #f8fafc;" id="adminEventsList">
                        <!-- Events injected via JS -->
                        <div style="padding:10px; text-align:center; font-size:12px; color:#94a3b8;">Cargando...</div>
                    </div>
                </div>"""

if target_cal_btn in content:
    content = content.replace(target_cal_btn, new_cal_btn)
    
if "loadAdminData();" in content and "loadCalendarEventsAdmin();" not in content:
    # Inject loadCalendarEventsAdmin into loadAdminData
    content = content.replace("loadAdminData() {", "loadAdminData() {\n            loadCalendarEventsAdmin();")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated rrhh.html for calendar admin")
