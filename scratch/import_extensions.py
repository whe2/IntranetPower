import sys
import os
import pandas as pd
import math

sys.path.append(r"c:\Users\wgallardo\Documents\Proyectos gravity\intranet")
from database import engine, Base, SessionLocal
import models

print("Creating tables if they don't exist...")
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    print("Reading Excel file...")
    file_path = r"C:\Users\wgallardo\Documents\extensiones asignadas.xlsx"
    df = pd.read_excel(file_path)
    
    current_dept = "GENERAL"
    extensions_added = 0
    
    db.query(models.PhoneExtension).delete()
    db.commit()
    
    print("Processing rows...")
    for index, row in df.iterrows():
        col0 = row.iloc[0]
        col1 = row.iloc[1]
        
        if pd.isna(col0):
            continue
            
        col0_str = str(col0).strip()
        
        if pd.isna(col1) or str(col1).strip() == "":
            current_dept = col0_str.upper()
            continue
            
        ext_str = str(col1).strip()
        
        is_group = False
        if "general" in col0_str.lower() or "grupo" in col0_str.lower():
            is_group = True
            
        try:
            if ext_str.endswith(".0"):
                ext_str = ext_str[:-2]
        except:
            pass
            
        ext = models.PhoneExtension(
            department=current_dept,
            name=col0_str,
            extension=ext_str,
            is_group=is_group
        )
        db.add(ext)
        extensions_added += 1
        
    db.commit()
    print(f"Success: {extensions_added} extensions imported to database!")

except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
