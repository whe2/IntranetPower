import paramiko

def fix_and_init():
    hostname = '10.0.1.179'
    username = 'root'
    password = 'Redes2010'

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f"Conectando a {hostname}...")
        client.connect(hostname, username=username, password=password, timeout=10)
        
        # PROD Fix and Init
        print("\n--- Corrigiendo .env e Inicializando PROD ---")
        cmd_prod_env = "echo 'DATABASE_URL=postgresql://intranet_user:Redes2010@localhost:5432/intranet_prod' > /var/www/intranet_prod/.env"
        client.exec_command(cmd_prod_env)
        
        cmd_prod_init = "cd /var/www/intranet_prod && source venv/bin/activate && python init_db.py"
        stdin, stdout, stderr = client.exec_command(f"bash -c '{cmd_prod_init}'")
        print(stdout.read().decode())
        print(stderr.read().decode())

        # QA Fix and Init
        print("\n--- Corrigiendo .env e Inicializando QA ---")
        cmd_qa_env = "echo 'DATABASE_URL=postgresql://intranet_user:Redes2010@localhost:5432/intranet_qa' > /var/www/intranet_qa/.env"
        client.exec_command(cmd_qa_env)
        
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
    fix_and_init()
