import os

file_path = r"c:\Users\wgallardo\Documents\Proyectos gravity\intranet\templates\rrhh.html"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update Departamento select
old_dept = """<select id="empDepartamento" class="form-control">
                            <option>Cargando departamentos...</option>
                        </select>"""
new_dept = """<select id="empDepartamento" class="form-control" onchange="checkNewDept(this)" required>
                            <option value="">Seleccione...</option>
                            {% for d in departments %}
                            <option value="{{ d.name }}">{{ d.name }}</option>
                            {% endfor %}
                            <option value="NEW_DEPT" style="font-weight:bold; color:#FCA311;">+ Crear Nuevo Departamento</option>
                        </select>"""
if old_dept in content:
    content = content.replace(old_dept, new_dept)

# 2. Add hidden ID to form and fix onsubmit
old_form_start = """<form id="addEmployeeForm" onsubmit="addEmployee(event)">"""
new_form_start = """<form id="addEmployeeForm" onsubmit="showSmtpModal(event)">
                    <input type="hidden" id="empId" value="">"""
if old_form_start in content:
    content = content.replace(old_form_start, new_form_start)

# 3. Add employee table to subtab-directorio
old_directorio = """<div id="subtab-directorio" class="subtab-content">
        <div style="padding: 60px; text-align: center; color: var(--texto-gris); background: var(--blanco); margin: 20px 30px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
            <i class="fa-solid fa-address-book" style="font-size: 3rem; margin-bottom: 15px; color: var(--texto-gris);"></i>
            <h2 style="color: var(--cabeceras); margin-bottom: 10px;">Gestión de Directorio</h2>
            <p>Esta sección se encuentra en desarrollo.</p>
        </div>
    </div>"""

new_directorio = """<div id="subtab-directorio" class="subtab-content">
        <div class="card" style="margin: 20px 30px;">
            <div class="section-title">
                <span><i class="fa-solid fa-address-book"></i> Directorio de Trabajadores</span>
            </div>
            <table style="width:100%; text-align:left; border-collapse: collapse; font-size:14px;">
                <thead>
                    <tr style="border-bottom:2px solid var(--acento);">
                        <th style="padding:10px;">Cédula</th>
                        <th>Nombre y Apellido</th>
                        <th>Departamento</th>
                        <th>Correo</th>
                        <th>Acciones</th>
                    </tr>
                </thead>
                <tbody>
                    {% for emp in employees %}
                    <tr style="border-bottom:1px solid #eee;">
                        <td style="padding:10px;">{{ emp.cedula }}</td>
                        <td>{{ emp.name }} {{ emp.apellido or '' }}</td>
                        <td>{{ emp.department }}</td>
                        <td>{{ emp.email }}</td>
                        <td>
                            <button onclick='editEmployee({{ emp.id }}, "{{ emp.cedula }}", "{{ emp.name }}", "{{ emp.apellido or "" }}", "{{ emp.email }}", "{{ emp.department }}", "{{ emp.birthday_date }}")' class="btn-action" style="padding:5px 10px; font-size:12px;">Editar</button>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>"""
if old_directorio in content:
    content = content.replace(old_directorio, new_directorio)

# 4. Add SMTP Modal before scripts
smtp_modal = """
    <!-- MODAL SMTP CREDENCIALES -->
    <div class="modal-overlay" id="smtpModal">
        <div class="modal-content" style="max-width: 400px;">
            <div class="modal-header">
                <h3><i class="fa-solid fa-envelope"></i> Enviar Bienvenida</h3>
                <button type="button" class="btn-close-modal" onclick="closeModal('smtpModal')"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <p style="font-size:13px; margin-bottom:15px;">Ingrese sus credenciales de SMTP para autorizar el envío del correo.</p>
            <form onsubmit="confirmAddEmployee(event)">
                <div class="form-group">
                    <label>Usuario SMTP</label>
                    <input type="text" id="smtpUser" class="form-control" required>
                </div>
                <div class="form-group">
                    <label>Contraseña SMTP</label>
                    <input type="password" id="smtpPass" class="form-control" required>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn-action" style="background:#ddd; color:#333;" onclick="closeModal('smtpModal')">Cancelar</button>
                    <button type="submit" class="btn-action btn-gold">Guardar y Enviar</button>
                </div>
            </form>
        </div>
    </div>
"""
# Append before closing body if comment not found
content = content.replace('</body>', smtp_modal + '\n</body>')

# 5. JS updates
js_additions = """
        function checkNewDept(select) {
            if (select.value === 'NEW_DEPT') {
                select.value = "";
                document.getElementById('deptModal').classList.add('active');
            }
        }
        
        function showSmtpModal(e) {
            e.preventDefault();
            document.getElementById('smtpModal').classList.add('active');
        }

        function editEmployee(id, cedula, name, apellido, email, dept, bday) {
            switchSubTab(event, 'subtab-rrhh'); // Switch back to HR tab
            document.getElementById('empId').value = id;
            document.getElementById('empCedula').value = cedula;
            document.getElementById('empNombre').value = name;
            document.getElementById('empApellido').value = apellido;
            document.getElementById('empEmail').value = email;
            document.getElementById('empDepartamento').value = dept;
            document.getElementById('empNacimiento').value = bday;
            document.getElementById('empUsuario').value = '';
            document.getElementById('empPassword').value = '';
            
            document.getElementById('empModal').classList.add('active');
        }

        async function confirmAddEmployee(e) {
            e.preventDefault();
            const form = document.getElementById('addEmployeeForm');
            
            const empId = document.getElementById('empId').value;
            const cedula = document.getElementById('empCedula').value;
            const name = document.getElementById('empNombre').value;
            const apellido = document.getElementById('empApellido').value;
            const email = document.getElementById('empEmail').value;
            const dept = document.getElementById('empDepartamento').value;
            const bday = document.getElementById('empNacimiento').value;
            
            const smtpUser = document.getElementById('smtpUser').value;
            const smtpPass = document.getElementById('smtpPass').value;

            const formData = new FormData();
            formData.append('cedula', cedula);
            formData.append('name', name);
            formData.append('apellido', apellido);
            formData.append('email', email);
            formData.append('department', dept);
            formData.append('position', 'Empleado');
            formData.append('birthday_date', bday);
            formData.append('smtp_user', smtpUser);
            formData.append('smtp_pass', smtpPass);
            
            const method = empId ? 'PUT' : 'POST';
            const url = empId ? `/api/rrhh/employees/${empId}` : '/api/rrhh/employees';

            try {
                const res = await fetch(url, { method: method, body: formData });
                if (res.ok) {
                    showToast('Empleado guardado y correo enviado.');
                    closeModal('smtpModal');
                    closeModal('empModal');
                    setTimeout(() => window.location.reload(), 1500);
                } else {
                    const data = await res.json();
                    alert(data.detail || 'Error al guardar el empleado.');
                }
            } catch (err) {
                console.error(err);
                alert('Error de red al guardar empleado.');
            }
        }
"""
content = content.replace('</script>\n</body>', js_additions + '\n</script>\n</body>')

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Template update completed!")
