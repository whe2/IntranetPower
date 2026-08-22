import os
import re

filepath = r"c:\Users\wgallardo\Documents\Proyectos gravity\intranet\templates\intranet.html"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Look for: document.getElementById('heroTitle').textContent = data.hero.title;
target = "document.getElementById('heroTitle').textContent = data.hero.title;"
replacement = """let heroTitleText = data.hero.title;
                    heroTitleText = heroTitleText.replace(/Sabina/gi, fullName.split(" ")[0]);
                    document.getElementById('heroTitle').textContent = heroTitleText;"""

if target in content:
    content = content.replace(target, replacement)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("Fixed intranet.html hero title.")
else:
    print("Target not found in intranet.html")

