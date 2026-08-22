import re

filepath = r"c:\Users\wgallardo\Documents\Proyectos gravity\intranet\templates\rrhh.html"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

target = """        async function addEmployee(e) {
            e.preventDefault();
            const cedula = document.getElementById('empCedula').value.trim();
            const nombre = document.getElementById('empNombre').value.trim();
            const apellido = document.getElementById('empApellido').value.trim();
            const name = `${nombre} ${apellido}`; 
            const position = document.getElementById('empDepartamento').value; 
            const birthday_date = document.getElementById('empNacimiento').value;
            const email = document.getElementById('empEmail').value.trim();
            const file = document.getElementById('empPhoto').files[0];
            const usuario = document.getElementById('empUsuario').value;
            const password = document.getElementById('empPassword').value;
            
            const formData = new FormData();
            formData.append('name', name);
            formData.append('cedula', cedula);
            formData.append('department', position);
            formData.append('position', 'Empleado'); // Default
            formData.append('birthday_date', birthday_date);
            formData.append('email', email);
            formData.append('usuario', usuario);
            formData.append('password', password);
            if (file) formData.append('photo', file);

            try {
                const res = await fetch('/api/rrhh/employees', { method: 'POST', body: formData });
                if (res.status === 400) {
                    const errorData = await res.json();
                    alert(errorData.detail || "Empleado ya se encuentra en sistema");
                    return;
                }
                if (res.ok) {
                    showToast('Empleado agregado al directorio.');
                    document.getElementById('addEmployeeForm').reset();
                    document.getElementById('empUsuario').value = '';
                    document.getElementById('empPassword').value = '';
                    closeModal('empModal');
                }
            } catch (e) { showToast('Error al guardar empleado', 'error'); }
        }"""

new_code = """        function showSmtpModal(e) {
            e.preventDefault();
            // Validate first
            const form = document.getElementById('addEmployeeForm');
            if(!form.checkValidity()) {
                form.reportValidity();
                return;
            }
            openModal('smtpModal');
        }

        async function confirmAddEmployee(e) {
            e.preventDefault();
            
            const smtpUser = document.getElementById('smtpUser').value.trim();
            const smtpPass = document.getElementById('smtpPass').value.trim();
            
            const cedula = document.getElementById('empCedula').value.trim();
            const nombre = document.getElementById('empNombre').value.trim();
            const apellido = document.getElementById('empApellido').value.trim();
            const position = document.getElementById('empDepartamento').value; 
            const birthday_date = document.getElementById('empNacimiento').value;
            const email = document.getElementById('empEmail').value.trim();
            const file = document.getElementById('empPhoto').files[0];
            const usuario = document.getElementById('empUsuario').value;
            const password = document.getElementById('empPassword').value;
            
            const formData = new FormData();
            formData.append('name', nombre);
            formData.append('apellido', apellido);
            formData.append('cedula', cedula);
            formData.append('department', position);
            formData.append('position', 'Empleado');
            formData.append('birthday_date', birthday_date);
            formData.append('email', email);
            formData.append('usuario', usuario);
            formData.append('password', password);
            formData.append('smtp_user', smtpUser);
            formData.append('smtp_pass', smtpPass);
            if (file) formData.append('photo', file);

            try {
                const res = await fetch('/api/rrhh/employees', { method: 'POST', body: formData });
                if (res.status === 422) {
                    showToast("Faltan datos requeridos", "error");
                    return;
                }
                if (res.status === 400) {
                    const errorData = await res.json();
                    showToast(errorData.detail || "Empleado ya se encuentra en sistema", "error");
                    return;
                }
                if (res.ok) {
                    showToast('Empleado agregado con éxito y credenciales enviadas.');
                    document.getElementById('addEmployeeForm').reset();
                    document.getElementById('empUsuario').value = '';
                    document.getElementById('empPassword').value = '';
                    document.getElementById('smtpUser').value = '';
                    document.getElementById('smtpPass').value = '';
                    closeModal('smtpModal');
                    closeModal('empModal');
                    loadAdminData(); // Refresh list
                } else {
                    showToast('Error en el servidor al agregar empleado', 'error');
                }
            } catch (err) { showToast('Error de red al guardar empleado', 'error'); }
        }"""

if target in content:
    content = content.replace(target, new_code)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("Success: replaced addEmployee with showSmtpModal and confirmAddEmployee.")
else:
    print("Target block not found precisely!")
