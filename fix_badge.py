import os

def fix_badge_color(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # We look for `.navbar .admin-badge {` and replace `color: var(--texto-negro);` with `color: var(--texto-negro) !important;`
    target1 = 'color: var(--texto-negro);'
    target2 = 'color: var(--texto-negro) !important;'
    
    if target2 not in content:
        # To be safe, only replace it if it's inside the .admin-badge block
        import re
        content = re.sub(r'(\.navbar \.admin-badge\s*\{[^}]*?color:\s*var\(--texto-negro\))(;)', r'\1 !important\2', content)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Fixed badge color in {filepath}")
    else:
        print(f"Already fixed in {filepath}")

fix_badge_color(r"c:\Users\wgallardo\Documents\Proyectos gravity\intranet\templates\rrhh.html")
fix_badge_color(r"c:\Users\wgallardo\Documents\Proyectos gravity\intranet\templates\intranet.html")
fix_badge_color(r"c:\Users\wgallardo\Documents\Proyectos gravity\intranet\templates\integracion.html")
