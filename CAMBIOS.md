# Lex·ERP — Mejoras para responder al ingeniero

Este paquete contiene SOLO los archivos nuevos o modificados. Cópielos encima de su proyecto (respetando las carpetas) **en una rama aparte**, así producción no se toca hasta que usted decida.

> **Importante:** el código se escribió y revisó sin poder ejecutarlo (en el entorno donde se preparó no había acceso a PyPI/npm). Es obligatorio correr las pruebas y el build en su máquina ANTES de subir a `main`. Si algo falla, el error le dirá exactamente qué archivo ajustar.

## 1. Cómo aplicarlo (PowerShell, en la carpeta del repo)

```powershell
git checkout -b mejoras
# copie el contenido del ZIP encima del proyecto (sobrescribir)

# Backend
python manage.py makemigrations --check      # debe decir "No changes detected"
python manage.py migrate
$env:DATABASE_URL="sqlite:///prueba.db"       # opcional: si su usuario de Postgres no puede crear la BD de pruebas
python manage.py test                         # deben pasar todas

# Frontend
cd frontend
npm install
npm run build                                 # debe terminar sin errores
```

Solo cuando todo pase:

```powershell
git add .
git commit -m "Mejoras: radicado 23 digitos, plazos, notificaciones, historial, documentos, usuarios, recuperar clave, pruebas"
git push origin mejoras
# Para publicar: git checkout main; git merge mejoras; git push (y el remoto de Render)
```

Si `makemigrations --check` pide cambios, ejecute `python manage.py makemigrations` y suba también esos archivos (las migraciones 0005/0004/0002 se escribieron a mano).

## 2. Qué responde a cada observación del ingeniero

| Observación | Qué se hizo |
|---|---|
| Radicado de 20 dígitos, en Colombia son 23 | Validación estricta del radicado (23 dígitos: ciudad DANE 5 + corporación 2 + especialidad 2 + despacho 3 + año 4 + consecutivo 5 + recurso 2). Contador en el formulario. Datos demo con radicados válidos. |
| Sin lógica de negocio / sin cálculo de plazos | Calculadora de **días hábiles** con festivos de Colombia (Ley Emiliani + Semana Santa). Al crear una etapa se digita "días hábiles" y se calcula la fecha límite. Muestra "faltan N días / vencida hace N días". Endpoint `GET /api/plazos/calcular/?dias=10`. |
| Notificaciones hechas a mano | Se generan solas: audiencias próximas (3 días), plazos próximos/vencidos, facturas vencidas/por vencer (solo directivos). Sin duplicados. También por comando: `python manage.py generar_notificaciones`. |
| Sin documentos adjuntos | Adjuntar/descargar/eliminar documentos por expediente (PDF, Word, Excel, imágenes, texto; máx. 5 MB). |
| Sin historial visible | Pestaña "Historial de cambios" en el expediente: quién, cuándo, campo, valor anterior y nuevo. |
| Sin pruebas automatizadas | Suite de pruebas en cada app (`python manage.py test`): radicado, festivos, plazos, permisos por rol, historial, documentos, usuarios, recuperación, etc. |
| Recuperar contraseña | Pantallas `/recuperar` y `/restablecer/...`. Enlace con vigencia de 1 hora; no revela si el correo existe; limitado a 30 solicitudes/hora. |
| Validaciones y errores claros | Validaciones por campo en backend (clientes, facturas, audiencias, expedientes) y mensajes en español en todos los formularios. El login distingue credenciales malas, cuenta bloqueada y servidor dormido. |
| Gestión de usuarios desde la app | Pantalla **Usuarios** (solo administrador / socio director): crear, editar, cambiar rol, activar/desactivar y desbloquear acceso. |
| Sin anclaje a caso real | Comando `python manage.py cargar_demo` con 4 expedientes verosímiles (radicados válidos, etapas, audiencias, facturas). Ver sección 4. |

Además se corrigió un hueco de seguridad: **abogados y secretarios solo ven sus expedientes asignados** (y sus audiencias/facturas); administrador y socio director ven todo. Las facturas pagadas ahora alimentan "Ingresos (mes)" según su fecha de pago, y el panel muestra plazos vencidos.

## 3. Variables de entorno nuevas (todas opcionales)

| Variable | Para qué |
|---|---|
| `CARGAR_DEMO=1` | En el próximo deploy ejecuta `cargar_demo` (es idempotente). Quítela después. |
| `DEMO_PASSWORD` | Si se define, crea usuarios demo `socio.herrera`, `abogada.rojas`, `secretario.diaz` con esa clave (para mostrar roles). Sin ella, todo se asigna al superusuario. |
| `RESEND_API_KEY` | Envío real de correos de recuperación (Render gratis bloquea SMTP; se usa la API HTTPS de Resend). Sin ella, el correo solo queda en los logs. |
| `DEFAULT_FROM_EMAIL` | Remitente (con Resend, un dominio verificado o `onboarding@resend.dev` para pruebas). |
| `FRONTEND_URL` | URL del frontend para armar el enlace de recuperación (por defecto, el primer origen CORS). |

## 4. Para mostrarle al ingeniero

1. Crear expediente con radicado de 20 dígitos → rechazado con mensaje claro.
2. Agregar etapa "Contestación de demanda" con 10 días hábiles → fecha límite calculada saltando festivos.
3. Abrir el panel → notificaciones generadas solas.
4. Adjuntar un PDF; editar el expediente y mostrar el historial.
5. Entrar como abogada.rojas → solo ve sus expedientes. Entrar como socio → ve todo y tiene "Usuarios".
6. "¿Olvidó su contraseña?".

## 5. Limitaciones que debe conocer (dígalas usted primero)

- **No se ejecutó nada aquí**: las pruebas y el build deben correrse en su equipo (sección 1).
- Un expediente ya existente en producción con radicado de 20 dígitos seguirá existiendo, pero al editarlo se exigirá corregirlo a 23.
- El cálculo de plazos no considera vacancia judicial ni suspensiones de términos; es una ayuda, no sustituye la verificación del abogado.
- Los clientes no se filtran por rol (todos los usuarios ven la lista de clientes).
- Los documentos se guardan en la base de datos (límite 5 MB) porque el disco gratuito de Render es efímero; para producción real, use almacenamiento externo (S3 o similar).
- La BD gratuita de Render expira a los 30 días.
- Seguirá siendo una demostración hasta que **un abogado o secretario de juzgado lo use y lo valide**: eso es lo que el ingeniero pide primero. Pida una cita de 30 minutos con alguien del oficio, muéstrele el flujo y anote qué cambiaría.
- No hay pruebas automáticas del frontend.
