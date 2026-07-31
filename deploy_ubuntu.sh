#!/bin/bash
# ==============================================================================
# Script de Despliegue para Servidor Ubuntu 24.04 - PROD y QA
# ==============================================================================
# Este script:
# 1. Instala PostgreSQL y Python.
# 2. Crea las bases de datos intranet_prod e intranet_qa.
# 3. Configura las carpetas en /var/www/.
# 4. Configura Apache como Reverse Proxy para PROD (puerto 80) y QA (puerto 8080).
# 5. Configura Systemd para auto-inicio de los procesos de FastAPI.

set -e # Detener script ante cualquier error

echo "========================================"
echo " Iniciando Configuración del Servidor..."
echo "========================================"

# 1. Actualizar e Instalar Dependencias
echo "-> Actualizando paquetes e instalando PostgreSQL y Python..."
apt-get update -y
apt-get install -y postgresql postgresql-contrib python3 python3-pip python3-venv apache2 curl

# Habilitar módulos de proxy en Apache
echo "-> Habilitando módulos de Apache..."
a2enmod proxy
a2enmod proxy_http
a2enmod headers
systemctl restart apache2

# 2. Configurar Base de Datos
echo "-> Configurando PostgreSQL (intranet_prod, intranet_qa)..."
# Ejecutamos los comandos como el usuario postgres
sudo -u postgres psql -c "CREATE DATABASE intranet_prod;" || echo "La DB intranet_prod ya existe."
sudo -u postgres psql -c "CREATE DATABASE intranet_qa;" || echo "La DB intranet_qa ya existe."
sudo -u postgres psql -c "CREATE USER intranet_user WITH ENCRYPTED PASSWORD 'Redes2010';" || echo "El usuario ya existe."
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE intranet_prod TO intranet_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE intranet_qa TO intranet_user;"

# 3. Crear Estructura de Directorios
echo "-> Configurando carpetas en /var/www/..."
mkdir -p /var/www/intranet_prod
mkdir -p /var/www/intranet_qa

chown -R $USER:$USER /var/www/intranet_prod
chown -R $USER:$USER /var/www/intranet_qa

# Función para preparar un entorno
preparar_entorno() {
    local RUTA=$1
    echo "   Preparando entorno en $RUTA..."
    cd $RUTA
    # Si requirements.txt existe, instalamos dependencias
    if [ -f "requirements.txt" ]; then
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        pip install uvicorn
        deactivate
    else
        echo "   [!] requirements.txt no encontrado en $RUTA (deberás subir los archivos de tu proyecto aquí)."
    fi
}

preparar_entorno "/var/www/intranet_prod"
preparar_entorno "/var/www/intranet_qa"

# 4. Crear Archivos Systemd
echo "-> Configurando Systemd (Auto-arranque de las Apps)..."

cat <<EOF > /etc/systemd/system/intranet_prod.service
[Unit]
Description=Intranet Produccion
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/var/www/intranet_prod
Environment="PATH=/var/www/intranet_prod/venv/bin"
ExecStart=/var/www/intranet_prod/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000

[Install]
WantedBy=multi-user.target
EOF

cat <<EOF > /etc/systemd/system/intranet_qa.service
[Unit]
Description=Intranet QA
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/var/www/intranet_qa
Environment="PATH=/var/www/intranet_qa/venv/bin"
ExecStart=/var/www/intranet_qa/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8001

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable intranet_prod
systemctl enable intranet_qa
# Nota: Iniciarlos requerirá que el código fuente ya esté ahí, así que lo omitimos por ahora.
# systemctl start intranet_prod
# systemctl start intranet_qa

# 5. Configurar Apache (VirtualHosts)
echo "-> Configurando Apache (Proxy Inverso)..."

cat <<EOF > /etc/apache2/sites-available/intranet.conf
# Servidor de Produccion (Puerto 80)
<VirtualHost *:80>
    ServerName pow-intranet
    # Opcional: ServerAlias intranet.tuempresa.com
    
    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/
    
    ErrorLog \${APACHE_LOG_DIR}/prod-error.log
    CustomLog \${APACHE_LOG_DIR}/prod-access.log combined
</VirtualHost>
EOF

cat <<EOF > /etc/apache2/sites-available/intranet-qa.conf
# Modificar el archivo ports.conf para escuchar en 8080 temporalmente en este script
Listen 8080

# Servidor de QA (Puerto 8080)
<VirtualHost *:8080>
    ServerName pow-intranet-qa
    
    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8001/
    ProxyPassReverse / http://127.0.0.1:8001/
    
    ErrorLog \${APACHE_LOG_DIR}/qa-error.log
    CustomLog \${APACHE_LOG_DIR}/qa-access.log combined
</VirtualHost>
EOF

# Habilitar el puerto 8080 en Apache
if ! grep -q "Listen 8080" /etc/apache2/ports.conf; then
    echo "Listen 8080" >> /etc/apache2/ports.conf
fi

a2ensite intranet.conf
a2ensite intranet-qa.conf
systemctl restart apache2

echo "=========================================================================="
echo " CONFIGURACIÓN DEL SERVIDOR COMPLETADA"
echo "=========================================================================="
echo "Siguientes Pasos (Manuales):"
echo "1. Sube tu código a /var/www/intranet_prod y /var/www/intranet_qa"
echo "2. Crea los archivos .env en cada carpeta con DATABASE_URL="
echo "   PROD -> postgresql://intranet_user:Redes2010@localhost:5432/intranet_prod"
echo "   QA   -> postgresql://intranet_user:Redes2010@localhost:5432/intranet_qa"
echo "3. Entra a cada carpeta, ejecuta:"
echo "   source venv/bin/activate"
echo "   pip install -r requirements.txt"
echo "4. Inicia los servicios con:"
echo "   systemctl start intranet_prod"
echo "   systemctl start intranet_qa"
echo "=========================================================================="
