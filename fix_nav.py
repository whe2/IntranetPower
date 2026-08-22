import os
import re

def fix_navigation(filepath, is_js=False):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Add fast-links Inicio
    target = '<div class="fast-links">'
    if target in content and '<i class="fa-solid fa-house"></i> Inicio</a>' not in content:
        if is_js:
            link = '\n            <a href="/" class="subtab-btn"><i class="fa-solid fa-house"></i> Inicio</a>'
        else:
            link = '\n        <a href="/"><i class="fa-solid fa-house"></i> Inicio</a>'
        
        content = content.replace(target, target + link)
        print(f"Added Inicio link to {filepath}")

    # Make logo clickable
    logo_pattern = r'<div class="logo">([\s\S]*?)</div>\s*<div class="user-menu">'
    match = re.search(logo_pattern, content)
    if match:
        logo_content = match.group(1)
        replacement = f'<a href="/" class="logo" style="text-decoration:none; color:inherit;">{logo_content}</a>\n        <div class="user-menu">'
        content = content.replace(match.group(0), replacement)
        print(f"Made logo clickable in {filepath}")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

fix_navigation(r"c:\Users\wgallardo\Documents\Proyectos gravity\intranet\templates\rrhh.html", is_js=True)
fix_navigation(r"c:\Users\wgallardo\Documents\Proyectos gravity\intranet\templates\intranet.html", is_js=False)
fix_navigation(r"c:\Users\wgallardo\Documents\Proyectos gravity\intranet\templates\integracion.html", is_js=False)
