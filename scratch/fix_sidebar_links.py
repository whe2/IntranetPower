import re
import os

templates_dir = r"c:\Users\wgallardo\Documents\Proyectos gravity\intranet\templates"

for filename in os.listdir(templates_dir):
    if filename.endswith(".html"):
        filepath = os.path.join(templates_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        # The link looks like: <a href="/"><i class="fa-solid fa-address-book"></i> Directorio</a>
        # Or maybe some other variations. Let's just find the exact string.
        target = '<a href="/"><i class="fa-solid fa-address-book"></i> Directorio</a>'
        replacement = '<a href="/directorio"><i class="fa-solid fa-address-book"></i> Directorio</a>'
        
        if target in content:
            content = content.replace(target, replacement)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Fixed link in {filename}")
