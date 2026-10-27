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

# Despachos de la Rama Judicial (idempotente): carga el catálogo y pasa los juzgados antiguos al despacho real.
if [ -f despachos.txt ]; then
  python manage.py importar_despachos despachos.txt
  python manage.py reasignar_juzgados_antiguos --aplicar
fi
