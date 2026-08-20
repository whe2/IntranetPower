import paramiko

def check_remote_db():
    hostname = '10.0.1.179'
    username = 'root'
    password = 'Redes2010'

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f"Conectando a {hostname}...")
        client.connect(hostname, username=username, password=password, timeout=10)
        
        # Check PROD DB
        print("\n--- Consultando intranet_prod ---")
        cmd_prod = 'sudo -u postgres psql -d intranet_prod -c "SELECT id, username, email, role, is_active FROM users WHERE is_active=true;"'
        stdin, stdout, stderr = client.exec_command(cmd_prod)
        print(stdout.read().decode())
        err = stderr.read().decode()
        if err:
            print("Error:", err)

        # Check QA DB
        print("\n--- Consultando intranet_qa ---")
        cmd_qa = 'sudo -u postgres psql -d intranet_qa -c "SELECT id, username, email, role, is_active FROM users WHERE is_active=true;"'
        stdin, stdout, stderr = client.exec_command(cmd_qa)
        print(stdout.read().decode())
        err = stderr.read().decode()
        if err:
            print("Error:", err)

    except Exception as e:
        print(f"Error de conexión: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    check_remote_db()
