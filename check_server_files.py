import paramiko

def check_remote_files():
    hostname = '10.0.1.179'
    username = 'root'
    password = 'Redes2010'

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(hostname, username=username, password=password, timeout=10)
        
        print("\n--- Verificando /var/www/intranet_prod ---")
        stdin, stdout, stderr = client.exec_command("ls -la /var/www/intranet_prod")
        print(stdout.read().decode())
        
        print("\n--- Verificando /var/www/intranet_qa ---")
        stdin, stdout, stderr = client.exec_command("ls -la /var/www/intranet_qa")
        print(stdout.read().decode())

    except Exception as e:
        print(f"Error de conexión: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    check_remote_files()
