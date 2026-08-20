import paramiko

def init_remote_db():
    hostname = '10.0.1.179'
    username = 'root'
    password = 'Redes2010'

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f"Conectando a {hostname}...")
        client.connect(hostname, username=username, password=password, timeout=10)
        
        # Init PROD
        print("\n--- Inicializando Base de Datos: intranet_prod ---")
        cmd_prod = "cd /var/www/intranet_prod && source venv/bin/activate && python init_db.py"
        # We need to run it in bash for 'source' to work
        stdin, stdout, stderr = client.exec_command(f"bash -c '{cmd_prod}'")
        print(stdout.read().decode())
        err = stderr.read().decode()
        if err:
            print("Error/Warning:", err)

        # Init QA
        print("\n--- Inicializando Base de Datos: intranet_qa ---")
        cmd_qa = "cd /var/www/intranet_qa && source venv/bin/activate && python init_db.py"
        stdin, stdout, stderr = client.exec_command(f"bash -c '{cmd_qa}'")
        print(stdout.read().decode())
        err = stderr.read().decode()
        if err:
            print("Error/Warning:", err)
            
        print("\n--- Reiniciando servicios de systemd ---")
        client.exec_command("systemctl restart intranet_prod")
        client.exec_command("systemctl restart intranet_qa")
        print("Servicios reiniciados.")

    except Exception as e:
        print(f"Error de conexión: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    init_remote_db()
