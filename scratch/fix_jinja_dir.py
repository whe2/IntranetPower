import re

filepath = r"c:\Users\wgallardo\Documents\Proyectos gravity\intranet\templates\directorio.html"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

target = """                <div style="text-align: right;">
                    <strong style="display: block; font-size: 14px; color: var(--texto-negro);">{{ user.name }} {{ user.apellido }}</strong>
                    <span style="font-size: 12px; color: var(--texto-gris);">{{ user.department }}</span>
                </div>
                <img src="{{ user.photo_url or '/static/img/default-avatar.png' }}" alt="Perfil">"""

replacement = """                <div style="text-align: right;">
                    <strong style="display: block; font-size: 14px; color: var(--texto-negro);">{{ user.full_name }}</strong>
                    <span style="font-size: 12px; color: var(--texto-gris);">{{ user.role | capitalize }}</span>
                </div>
                <img src="{{ user.avatar_url or '/static/img/default-avatar.png' }}" alt="Perfil">"""

if target in content:
    content = content.replace(target, replacement)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("Fixed Jinja2 variables in directorio.html")
else:
    print("Target not found in directorio.html")
