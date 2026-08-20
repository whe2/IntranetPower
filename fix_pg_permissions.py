import paramiko

def fix_permissions_and_init():
    hostname = '10.0.1.179'
    username = 'root'
    password = 'Redes2010'

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f"Conectando a {hostname}...")
        client.connect(hostname, username=username, password=password, timeout=10)
        
        print("\n--- Arreglando permisos del schema public ---")
        client.exec_command('sudo -u postgres psql -d intranet_prod -c "GRANT ALL ON SCHEMA public TO intranet_user;"')
        client.exec_command('sudo -u postgres psql -d intranet_qa -c "GRANT ALL ON SCHEMA public TO intranet_user;"')
        
        print("\n--- Inicializando PROD ---")
        cmd_prod_init = "cd /var/www/intranet_prod && source venv/bin/activate && python init_db.py"
        stdin, stdout, stderr = client.exec_command(f"bash -c '{cmd_prod_init}'")
        print(stdout.read().decode())
        print(stderr.read().decode())

        print("\n--- Inicializando QA ---")
        cmd_qa_init = "cd /var/www/intranet_qa && source venv/bin/activate && python init_db.py"
        stdin, stdout, stderr = client.exec_command(f"bash -c '{cmd_qa_init}'")
        print(stdout.read().decode())
        print(stderr.read().decode())
            
        print("\n--- Reiniciando servicios de systemd ---")
        client.exec_command("systemctl restart intranet_prod")
        client.exec_command("systemctl restart intranet_qa")
        print("Servicios reiniciados.")

    except Exception as e:
        print(f"Error de conexión: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    fix_permissions_and_init()
