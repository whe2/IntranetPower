import os, glob

target = """        {% if user.role == 'admin' or 'cargar_datos_usuarios' in (user.permissions or '') %}
        <a href="/admin"><i class="fa-solid fa-users"></i> RRHH</a>
        {% endif %}"""

replacement = """        {% if user.role == 'admin' or 'cargar_datos_usuarios' in (user.permissions or '') %}
        <a href="/admin"><i class="fa-solid fa-users"></i> RRHH</a>
        {% endif %}
        {% if user.role == 'admin' %}
        <a href="/admin?tab=permisos"><i class="fa-solid fa-shield-halved"></i> Permisos</a>
        {% endif %}"""

for f in glob.glob('templates/*.html'):
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    if target in content:
        content = content.replace(target, replacement)
        with open(f, 'w', encoding='utf-8') as file:
            file.write(content)
        print('Updated ' + f)
