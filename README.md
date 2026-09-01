# MercaGo · MVP Django

MercaGo es una experiencia móvil integrada visualmente en un Home inspirado en Yango. Solo **MercaGo** es funcional; Comida, Bike, Envíos, Viajes, Tiendas, Lugares, Transporte, Navegador y Cargo son elementos visuales que muestran “Próximamente”.

## Funcionalidad incluida

- Home mobile-first con paleta Yango y MercaGo en el carrusel de servicios.
- Mercado Abasto, 7 categorías y 19 productos demo.
- Búsqueda y filtro por categoría.
- Lista de compra con cantidades y subtotal estimado.
- Mínimo de compra de Bs 250, visible y validado también en el servidor.
- Desglose de costos con Bs 15 de servicio MercaGo y Bs 15 de envío.
- Registro y selección de ubicaciones de entrega con nombre, dirección y referencia.
- Preferencias de madurez, tamaño, calidad, sustitución, tolerancia de precio y notas.
- Selección de dirección, fecha futura y ventana de entrega.
- Creación de pedido, historial y seguimiento visual.
- Incidencias de cambio de precio, agotado y sustitución desde Django Admin.
- Aceptación o rechazo de incidencias por el cliente.

## Puesta en marcha

Requiere Python 3.10+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data
python manage.py createsuperuser
python manage.py runserver
```

Abre `http://127.0.0.1:8000/`.

## Administración

- URL: `http://127.0.0.1:8000/admin/`
- Crea un administrador seguro con `python manage.py createsuperuser`.
- Para automatizar datos demo puedes definir temporalmente `MERCAGO_ADMIN_PASSWORD` antes de ejecutar `seed_data`; nunca publiques esa contraseña.

Después de crear un pedido como cliente, entra al Admin y:

1. Cambia el estado del pedido para simular el flujo operativo.
2. En **Incidencias**, crea una vinculada a uno de sus productos.
3. El pedido pasa automáticamente a **Esperando tu aprobación**.
4. Vuelve al seguimiento del cliente y acepta o rechaza la propuesta.

## Alcance intencional

No hay pagos, GPS, mapas reales, APIs de Yango, notificaciones push ni frameworks frontend. SQLite y Django Templates mantienen el MVP fácil de demostrar y extender.

## Despliegue en subdominio

La carpeta `deploy/` contiene ejemplos independientes para Gunicorn, systemd y Nginx. Consulta `deploy/DEPLOY.md` antes de publicar; no uses `runserver` en producción.
