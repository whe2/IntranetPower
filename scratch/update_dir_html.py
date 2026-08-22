import re

filepath = r"c:\Users\wgallardo\Documents\Proyectos gravity\intranet\templates\directorio.html"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

target = """            <h1 class="page-title">Extensiones Powerlink</h1>
            <p class="page-subtitle">Encuentra los números de anexo para comunicarte con cada departamento de la empresa.</p>
            
            <div class="search-container">"""

replacement = """            <h1 class="page-title">Directorio de Trabajadores</h1>
            <p class="page-subtitle">Consulta la información de contacto de todos los miembros del equipo.</p>
            
            <div style="background: white; border-radius: 12px; padding: 20px; margin-bottom: 40px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); overflow-x: auto;">
                <table style="width:100%; text-align:left; border-collapse: collapse; font-size:14px;">
                    <thead>
                        <tr style="border-bottom:2px solid var(--acento);">
                            <th style="padding:12px; color:var(--texto-negro);">Nombre y Apellido</th>
                            <th style="padding:12px; color:var(--texto-negro);">Departamento</th>
                            <th style="padding:12px; color:var(--texto-negro);">Correo Electrónico</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for emp in employees %}
                        <tr style="border-bottom:1px solid #f1f5f9; transition: background 0.2s;">
                            <td style="padding:12px;">
                                <div style="display:flex; align-items:center; gap:10px;">
                                    <img src="{{ emp.photo_url or '/static/img/default-avatar.png' }}" style="width:32px; height:32px; border-radius:50%; object-fit:cover;">
                                    <strong style="color:var(--texto-negro);">{{ emp.name }} {{ emp.apellido or '' }}</strong>
                                </div>
                            </td>
                            <td style="padding:12px; color:var(--texto-gris);">{{ emp.department }}</td>
                            <td style="padding:12px; color:var(--texto-gris);"><a href="mailto:{{ emp.email }}" style="color:var(--bento-verde); text-decoration:none;">{{ emp.email }}</a></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>

            <h1 class="page-title">Extensiones Powerlink</h1>
            <p class="page-subtitle">Encuentra los números de anexo para comunicarte con cada departamento de la empresa.</p>
            
            <div class="search-container">"""

if target in content:
    content = content.replace(target, replacement)
    
    # Also add a hover effect to the table rows in the css block
    css_target = ".bento-grid {"
    css_replacement = """tbody tr:hover {
            background-color: #f8fafc;
        }
        
        .bento-grid {"""
    content = content.replace(css_target, css_replacement)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated directorio.html with employee table")
else:
    print("Target not found in directorio.html")
