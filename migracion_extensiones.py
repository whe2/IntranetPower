import json
import sys
from database import SessionLocal
import models

def export_data():
    db = SessionLocal()
    extensions = db.query(models.PhoneExtension).all()
    data = []
    for ext in extensions:
        data.append({
            "department": ext.department,
            "name": ext.name,
            "extension": ext.extension,
            "is_group": ext.is_group
        })
    db.close()
    
    with open("extensiones.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Exportadas {len(data)} extensiones a extensiones.json")

def import_data():
    try:
        with open("extensiones.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error leyendo extensiones.json: {e}")
        return

    db = SessionLocal()
    # Limpiamos las extensiones viejas si quisieran reemplazar o solo añadimos si no existen.
    # Por seguridad, si ya existen, las omitiremos.
    existing = {ext.extension for ext in db.query(models.PhoneExtension).all()}
    count = 0
    for item in data:
        if item["extension"] not in existing:
            new_ext = models.PhoneExtension(
                department=item.get("department", ""),
                name=item.get("name", ""),
                extension=item.get("extension", ""),
                is_group=item.get("is_group", False)
            )
            db.add(new_ext)
            count += 1
            existing.add(item["extension"])
            
    db.commit()
    db.close()
    print(f"Importadas {count} nuevas extensiones.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "import":
        import_data()
    else:
        export_data()
