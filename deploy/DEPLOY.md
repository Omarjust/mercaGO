# Publicar MercaGo en un subdominio con Nginx

Los ejemplos aíslan MercaGo mediante su propio servicio systemd y socket Unix. La aplicación Django que ya existe en el servidor conserva su configuración, puerto o socket.

Esta guía ya está configurada para:

- Subdominio: `mercago.yellowmarket.lat`.
- Ruta: `/srv/mercago/app`.
- Usuario Linux: `deploy`.
- Sistema: Debian con Nginx.

## 1. DNS

En el proveedor DNS crea un registro:

```text
Tipo: A
Nombre: mercago
Valor: IP pública del servidor Debian
Proxy: DNS only (nube gris) durante la instalación
TTL: Auto
```

Si el servidor usa IPv6, agrega además un registro `AAAA`. El registro DNS solo dirige el nombre; no reemplaza la configuración de Nginx.

Los nameservers de `yellowmarket.lat` están en Cloudflare, por lo que este registro debe crearse en **Cloudflare → yellowmarket.lat → DNS → Records**, no en la pantalla del registrador mostrada en la captura.

Comprueba la propagación antes de continuar:

```bash
dig +short mercago.yellowmarket.lat
```

Debe mostrar la IP pública del servidor.

## 2. Instalar la aplicación en Debian

Ejemplo para `/srv/mercago/app`:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip nginx certbot python3-certbot-nginx
sudo mkdir -p /srv/mercago/app /srv/mercago/shared /etc/mercago
sudo chown -R deploy:www-data /srv/mercago
cd /srv/mercago/app
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Copia el proyecto a esa ruta. Mantén `db.sqlite3` en `/srv/mercago/shared/` para que una actualización del código no lo reemplace.

## 3. Variables de producción

Copia `.env.production.example` a `/etc/mercago/mercago.env`, reemplaza el subdominio y genera una clave nueva:

```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(64))'
sudo chmod 640 /etc/mercago/mercago.env
sudo chown root:www-data /etc/mercago/mercago.env
```

No publiques ese archivo ni reutilices la clave de desarrollo.

## 4. Base de datos y archivos estáticos

```bash
cd /srv/mercago/app
set -a
source /etc/mercago/mercago.env
set +a
.venv/bin/python manage.py migrate
.venv/bin/python manage.py collectstatic --noinput
.venv/bin/python manage.py check --deploy
```

Ejecuta `seed_data` solo si deseas cargar o actualizar los datos demostrativos. Crea el administrador con `manage.py createsuperuser` y una contraseña privada.

## 5. Servicio systemd independiente

Copia `deploy/mercago.service.example` a `/etc/systemd/system/mercago.service`; ya contiene el usuario `deploy` y la ruta `/srv/mercago/app`:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now mercago
sudo systemctl status mercago
```

El socket propio queda en `/run/mercago/gunicorn.sock`, por lo que no choca con la otra aplicación Django.

## 6. Bloque Nginx del subdominio

Copia `deploy/nginx-mercago.conf.example` a `/etc/nginx/sites-available/mercago`; ya contiene `mercago.yellowmarket.lat` y la ruta correcta:

```bash
sudo ln -s /etc/nginx/sites-available/mercago /etc/nginx/sites-enabled/mercago
sudo nginx -t
sudo systemctl reload nginx
```

No recargues Nginx si `nginx -t` informa un error.

## 7. HTTPS

Cuando el DNS ya apunte al servidor y el sitio responda por HTTP:

```bash
sudo certbot --nginx -d mercago.yellowmarket.lat
sudo nginx -t
sudo systemctl reload nginx
```

Usa siempre `http://` antes de instalar el certificado y `https://` después. Comprueba también la renovación de Certbot según la instalación del servidor.

Cuando HTTPS funcione correctamente, puedes volver a Cloudflare y activar la nube naranja. En **SSL/TLS**, usa `Full (strict)` si Cloudflare administra el tráfico del subdominio.

## Actualizaciones posteriores

```bash
cd /srv/mercago/app
.venv/bin/pip install -r requirements.txt
set -a
source /etc/mercago/mercago.env
set +a
.venv/bin/python manage.py migrate
.venv/bin/python manage.py collectstatic --noinput
sudo systemctl restart mercago
sudo systemctl status mercago
```

Antes de cada actualización realiza una copia de `/srv/mercago/shared/db.sqlite3`.
