import re

filepath = r"c:\Users\wgallardo\Documents\Proyectos gravity\intranet\templates\rrhh.html"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Replace HTML
target_html = """                <!-- GESTIONAR DEPARTAMENTOS -->
                <div class="card">
                    <div class="section-title">🏢 Gestionar Departamentos</div>
                    <button class="btn-action" style="width:100%; background-color:#334155;" onclick="openModal('deptModal')">
                        <i class="fa-solid fa-folder-plus"></i> Crear Departamento
                    </button>
                </div>"""

new_html = """                <!-- GESTIONAR DEPARTAMENTOS -->
                <div class="card">
                    <div class="section-title">🏢 Gestionar Departamentos</div>
                    <button class="btn-action" style="width:100%; background-color:#334155; margin-bottom: 12px;" onclick="openModal('deptModal')">
                        <i class="fa-solid fa-folder-plus"></i> Crear Departamento
                    </button>
                    <div style="max-height: 140px; overflow-y: auto; border: 1px solid #e2e8f0; border-radius: 8px; background-color: #f8fafc;">
                        <ul id="deptListContainer" style="list-style: none; padding: 0; margin: 0;">
                            <!-- Insertado por JS -->
                            <li style="padding:10px; text-align:center; font-size:12px; color:#94a3b8;"><i class="fa-solid fa-spinner fa-spin"></i> Cargando...</li>
                        </ul>
                    </div>
                </div>"""

content = content.replace(target_html, new_html)

# Add CSS
css_injection = """
        #deptListContainer li {
            padding: 10px 12px;
            border-bottom: 1px solid #e2e8f0;
            font-size: 13px;
            color: var(--texto-negro);
            display: flex;
            align-items: center;
            gap: 10px;
            font-weight: 500;
        }
        #deptListContainer li:last-child {
            border-bottom: none;
        }
        #deptListContainer li i {
            color: var(--acento);
            font-size: 14px;
        }
"""
content = content.replace("</style>", css_injection + "\n    </style>")


# Modify JS
js_target = """                    deps.forEach(d => {
                        const opt = document.createElement('option');
                        opt.value = d.name;
                        opt.textContent = d.name;
                        select.appendChild(opt);
                    });
                }"""

js_new = """                    const deptListContainer = document.getElementById('deptListContainer');
                    deptListContainer.innerHTML = '';
                    
                    // Ordenamos para mostrar los ultimos creados primero (asumiendo que vienen en orden o invertimos)
                    const reversedDeps = [...deps].reverse();
                    
                    reversedDeps.forEach(d => {
                        // Para el select
                        const opt = document.createElement('option');
                        opt.value = d.name;
                        opt.textContent = d.name;
                        select.appendChild(opt);
                        
                        // Para la lista visual
                        const li = document.createElement('li');
                        li.innerHTML = `<i class="fa-solid fa-building"></i> ${d.name}`;
                        deptListContainer.appendChild(li);
                    });
                    
                    if (reversedDeps.length === 0) {
                        deptListContainer.innerHTML = '<li style="padding:10px; text-align:center; font-size:12px; color:#94a3b8;">No hay departamentos</li>';
                    }
                }"""

content = content.replace(js_target, js_new)


with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Changes applied!")
