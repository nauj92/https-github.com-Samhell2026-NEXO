#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

python manage.py createsuperuser --no-input || true

# Datos de demostración (opcional): defina CARGAR_DEMO=1 en las variables de entorno de Render.
# Es idempotente. Si define DEMO_PASSWORD también crea usuarios de ejemplo (socio, abogada, secretario).
if [ "${CARGAR_DEMO:-}" = "1" ]; then
  python manage.py cargar_demo
fi
