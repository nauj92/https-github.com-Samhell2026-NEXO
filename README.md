# ⚖️ ERP — Sistema de Gestión Judicial (ERP Operador Judicial)

Sistema de administración de gestión jurídica para despachos de abogados. Permite gestionar expedientes, audiencias, clientes, facturación y notificaciones, con control de acceso por roles y trazabilidad de cambios.

## 📋 Descripción general

ERP centraliza el flujo de trabajo de un despacho jurídico:

- **Expedientes**: registro y seguimiento de casos judiciales, con etapas del proceso (timeline).
- **Audiencias**: agenda de audiencias vinculadas a cada expediente.
- **Clientes**: base de datos de clientes del despacho.
- **Facturación**: control de facturas emitidas, su estado y vencimiento.
- **Notificaciones**: alertas internas para los usuarios (audiencias próximas, plazos, facturas).
- **Panel de control**: estadísticas en tiempo real (casos activos, ingresos del mes, distribución por materia).

El sistema separa dos capas independientes:

| Capa | Tecnología | Función |
|---|---|---|
| Backend | Django + Django REST Framework | Lógica de negocio, base de datos, API REST, seguridad |
| Frontend | React + Vite | Interfaz visual que consume la API |

## 🧱 Arquitectura y estructura del proyecto

-----------------------------------------------------------------------------------------------------------------------------------

erp-operador-judicial/
├── config/ # Configuración del proyecto Django
│ ├── settings/
│ │ ├── base.py # Configuración común
│ │ ├── dev.py # Configuración de desarrollo
│ │ └── prod.py # Configuración de producción
│ └── urls.py # Enrutamiento principal de la API
├── usuarios/ # Modelo de usuario personalizado, con roles
├── expedientes/ # Expedientes, Juzgados, Etapas del proceso
├── audiencias/ # Audiencias judiciales
├── clientes/ # Clientes del despacho
├── facturacion/ # Facturas
├── notificaciones/ # Notificaciones internas
├── core/ # Utilidades compartidas
├── frontend/ # Aplicación React (interfaz de usuario)
│ ├── src/
│ │ ├── pages/ # Pantallas: Login, Dashboard, Expedientes, etc.
│ │ ├── components/ # Sidebar, Layout
│ │ └── api.js # Cliente HTTP con autenticación JWT
│ └── package.json
├── requirements.txt # Dependencias de Python
├── manage.py
└── .env # Variables de entorno (NO se sube al repositorio)

-----------------------------------------------------------------------------------------------------------------------------------

## ⚙️ Requisitos previos

- Python 3.11 o superior
- Node.js 22 LTS o superior
- PostgreSQL 15 o superior
- Git

## 🗄️ Modelo de base de datos

Motor: **PostgreSQL**.

Entidades principales:

- `Usuario` (extiende el usuario de Django, agrega `rol` y `telefono`)
- `Juzgado`
- `Expediente` (con historial de auditoría vía `django-simple-history`)
- `EtapaProceso` (relacionado con `Expediente`)
- `Audiencia` (relacionado con `Expediente`)
- `Cliente`
- `Factura` (relacionado opcionalmente con `Expediente`)
- `Notificacion` (relacionado con `Usuario`)

Todas las tablas de seguridad de `django-axes` (control de intentos de acceso) también forman parte del esquema.

## 🚀 Instalación y configuración del entorno

### 1. Clona el repositorio

```bash
git clone https://github.com/Samhell2026/ERP-OPERADOR-JUDICIAL-.git
cd ERP-OPERADOR-JUDICIAL-
```

### 2. Backend (Django)

Crea y activa el entorno virtual:

```bash
python -m venv venv
# Windows
venv\Scripts\Activate.ps1
# Linux/Mac
source venv/bin/activate
```

Instala las dependencias:

```bash
pip install -r requirements.txt
```

Crea el archivo `.env` en la raíz del proyecto con el siguiente contenido (ajusta los valores a tu entorno):

---------------------------------------------------------------------------------------------------------------------------------

DEBUG=True
SECRET_KEY=genera-una-clave-larga-y-aleatoria
DATABASE_URL=postgres://usuario:password@localhost:5432/erp_judicial
ALLOWED_HOSTS=localhost,127.0.0.1

--------------------------------------------------------------------------------------------------------------------------------


Para generar una `SECRET_KEY` segura:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 3. Base de datos

Crea la base de datos en PostgreSQL:

```sql
CREATE DATABASE erp_judicial;
```

Aplica las migraciones:

```bash
python manage.py migrate
```

Crea un superusuario:

```bash
python manage.py createsuperuser
```

### 4. Levanta el servidor de Django

```bash
python manage.py runserver
```

La API queda disponible en `http://127.0.0.1:8000/` y el panel de administración en `http://127.0.0.1:8000/admin/`.

### 5. Frontend (React)

En otra terminal:

```bash
cd frontend
npm install
npm run dev
```

La aplicación queda disponible en `http://localhost:5173/`.

## 🔐 Seguridad implementada

- Autenticación por **JWT** (`djangorestframework-simplejwt`), con renovación automática de token en el frontend.
- **django-axes**: bloqueo de cuentas tras intentos fallidos de inicio de sesión (por usuario e IP).
- **django-simple-history**: auditoría de cambios sobre el modelo `Expediente` (quién cambió qué y cuándo).
- **Permisos por rol**: los usuarios con rol `abogado` o `secretario_juridico` solo ven los expedientes que tienen asignados; `administrador` y `socio_director` ven todos.
- Variables sensibles (contraseñas, claves) fuera del control de versiones mediante `.env` y `.gitignore`.

## 🛣️ Endpoints principales de la API

| Endpoint | Método | Descripción |
|---|---|---|
| `/api/token/` | POST | Inicio de sesión (obtiene access y refresh token) |
| `/api/token/refresh/` | POST | Renueva el access token |
| `/api/expedientes/` | GET, POST | Listar / crear expedientes |
| `/api/expedientes/{id}/` | GET, PATCH, DELETE | Detalle / editar / eliminar expediente |
| `/api/audiencias/` | GET, POST | Listar / crear audiencias |
| `/api/clientes/` | GET, POST | Listar / crear clientes |
| `/api/facturas/` | GET, POST | Listar / crear facturas |
| `/api/notificaciones/` | GET | Notificaciones del usuario autenticado |
| `/api/dashboard/stats/` | GET | Estadísticas del panel de control |

## 👥 Roles de usuario

| Rol | Alcance |
|---|---|
| `administrador` | Acceso total al sistema |
| `socio_director` | Acceso total al sistema |
| `abogado` | Solo sus expedientes asignados |
| `secretario_juridico` | Solo expedientes asignados |

## 🧩 Estado del proyecto

- [x] Backend: usuarios, expedientes, audiencias, clientes, facturación, notificaciones
- [x] API REST con autenticación JWT
- [x] Seguridad: axes, auditoría, permisos por rol
- [x] Frontend: login, dashboard, CRUD completo en los 4 módulos principales
- [ ] Despliegue en producción
- [ ] Pruebas automatizadas

## 👤 Autor

Proyecto desarrollado como parte del Semillero de Ingeniería de Software.
