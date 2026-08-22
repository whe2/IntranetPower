
with open(r"c:\Users\wgallardo\Documents\Proyectos gravity\intranet\models.py", "a") as f:
    f.write("\n\nclass PhoneExtension(Base):\n")
    f.write("    __tablename__ = 'phone_extensions'\n\n")
    f.write("    id = Column(Integer, primary_key=True, index=True)\n")
    f.write("    department = Column(String, index=True)\n")
    f.write("    name = Column(String)\n")
    f.write("    extension = Column(String)\n")
    f.write("    is_group = Column(Boolean, default=False)\n")

print("Added PhoneExtension to models.py")
