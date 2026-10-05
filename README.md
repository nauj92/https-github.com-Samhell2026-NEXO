# ⚖️ ERP — Sistema de Gestión Judicial (NEXO / ERP Operador Judicial)

Sistema de administración de gestión jurídica para despachos de abogados. Permite gestionar expedientes, audiencias, clientes, facturación y notificaciones, con control de acceso por roles y trazabilidad de cambios.

Proyecto desarrollado en el marco del **Semillero de Ingeniería de Software**.

---

## 📋 Descripción general

Lex·ERP centraliza el flujo de trabajo de un despacho jurídico:

- **Expedientes**: registro y seguimiento de casos judiciales, con etapas del proceso (línea de tiempo).
- **Audiencias**: agenda de audiencias vinculadas a cada expediente.
- **Clientes**: base de datos de clientes del despacho, relacionada formalmente con expedientes y facturas.
- **Facturación**: control de facturas emitidas, su estado y vencimiento.
- **Notificaciones**: alertas internas para los usuarios (audiencias próximas, plazos, facturas).
- **Panel de control**: estadísticas en tiempo real (casos activos, ingresos del mes, distribución por materia).
- **Reportes**: analítica de rendimiento por abogado y ranking de clientes por facturación.

El sistema separa dos capas independientes, comunicadas mediante una API REST:

| Capa | Función |
|---|---|
| Backend | Lógica de negocio, base de datos, API REST, seguridad |
| Frontend | Interfaz visual que consume la API |

---

## 🧰 Lenguajes y Tecnologías Utilizadas

### Backend
| Tecnología | Uso |
|---|---|
| **Python 3.13** | Lenguaje principal del backend |
| **Django 6.1** | Framework web principal |
| **Django REST Framework** | Construcción de la API REST |
| **djangorestframework-simplejwt** | Autenticación mediante JWT |
| **django-axes** | Bloqueo por intentos fallidos de inicio de sesión |
| **django-simple-history** | Auditoría de cambios sobre expedientes |
| **django-cors-headers** | Control de CORS entre frontend y backend |
| **psycopg2-binary** | Conector de PostgreSQL para Python |
| **PostgreSQL 17** | Motor de base de datos relacional |

### Frontend
| Tecnología | Uso |
|---|---|
| **JavaScript (JSX)** | Lenguaje principal del frontend |
| **React 18** | Librería de interfaz de usuario |
| **Vite** | Herramienta de construcción y servidor de desarrollo |
| **React Router DOM** | Enrutamiento entre pantallas |
| **Axios** | Cliente HTTP para consumir la API |
| **Recharts** | Gráficos de estadísticas (panel de control) |
| **lucide-react** | Librería de íconos |

### Herramientas de desarrollo
- **Git / GitHub** — control de versiones
- **Visual Studio Code** — entorno de desarrollo
- **Postman** — pruebas de la API REST

---

## 🧱 Arquitectura y estructura del proyecto

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
│ │ ├── pages/ # Login, Dashboard, Expedientes, etc.
│ │ ├── components/ # Sidebar, Layout
│ │ └── api.js # Cliente HTTP con autenticación JWT
│ └── package.json
├── requirements.txt # Dependencias de Python
├── manage.py
└── .env # Variables de entorno (NO se sube al repositorio)


---

## 🗄️ Modelo de Base de Datos

Motor: **PostgreSQL 17**.

### Entidades principales

- **Usuario** — extiende el usuario de Django, agrega `rol` y `telefono`.
- **Juzgado** — nombre, ciudad, materia.
- **Expediente** — entidad central, con historial de auditoría (`django-simple-history`).
- **EtapaProceso** — etapas del proceso judicial, relacionadas con un Expediente.
- **Audiencia** — relacionada con un Expediente.
- **Cliente** — relacionado formalmente con Expediente y Factura.
- **Factura** — relacionada opcionalmente con Expediente, y con Cliente.
- **Notificacion** — relacionada con Usuario.

### Diagrama de Entidad-Relación

```mermaid
erDiagram
    USUARIO ||--o{ EXPEDIENTE : "abogado_asignado"
    USUARIO ||--o{ NOTIFICACION : "recibe"
    JUZGADO ||--o{ EXPEDIENTE : "tramita"
    CLIENTE ||--o{ EXPEDIENTE : "representa"
    CLIENTE ||--o{ FACTURA : "factura"
    EXPEDIENTE ||--o{ ETAPAPROCESO : "contiene"
    EXPEDIENTE ||--o{ AUDIENCIA : "tiene"
    EXPEDIENTE ||--o{ FACTURA : "genera"

    USUARIO {
        int id PK
        string username
        string email
        string first_name
        string last_name
        string rol
        string telefono
    }

    JUZGADO {
        int id PK
        string nombre
        string ciudad
        string materia
    }

    CLIENTE {
        int id PK
        string nombre
        string tipo_documento
        string numero_documento
        string telefono
        string email
        string direccion
    }

    EXPEDIENTE {
        int id PK
        string numero
        int juzgado_id FK
        int cliente_id FK
        string demandante
        string demandado
        string materia
        string estado
        int abogado_asignado_id FK
        datetime creado_en
    }

    ETAPAPROCESO {
        int id PK
        int expediente_id FK
        string nombre
        date fecha_limite
        string estado
        int orden
    }

    AUDIENCIA {
        int id PK
        int expediente_id FK
        datetime fecha_hora
        string lugar
        string observaciones
    }

    FACTURA {
        int id PK
        string numero
        int expediente_id FK
        int cliente_id FK
        string concepto
        decimal monto
        string estado
        date fecha_emision
        date fecha_vencimiento
    }

    NOTIFICACION {
        int id PK
        int usuario_id FK
        string tipo
        string mensaje
        boolean leida
        datetime creada_en
    }
```

> El diagrama anterior está escrito en sintaxis **Mermaid**; GitHub lo renderiza automáticamente como diagrama visual al visualizar este archivo.

Todas las tablas de seguridad de **django-axes** (control de intentos de acceso) también forman parte del esquema.

---

## ⚙️ Requisitos previos

- Python 3.11 o superior
- Node.js 22 LTS o superior
- PostgreSQL 15 o superior
- Git

---

## 🚀 Instalación y configuración del entorno

### 1. Clona el repositorio

```bash
git clone https://github.com/Samhell2026/NEXO.git
cd NEXO
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

Crea el archivo `.env` en la raíz del proyecto:

DEBUG=True
SECRET_KEY=genera-una-clave-larga-y-aleatoria
DATABASE_URL=postgres://usuario:password@localhost:5432/erp_judicial
ALLOWED_HOSTS=localhost,127.0.0.1


Genera una `SECRET_KEY` segura:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 3. Base de datos

```sql
CREATE DATABASE erp_judicial;
```

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4. Levanta el servidor de Django

```bash
python manage.py runserver
```

API: `http://127.0.0.1:8000/` · Admin: `http://127.0.0.1:8000/admin/`

### 5. Frontend (React)

```bash
cd frontend
npm install
npm run dev
```

Aplicación: `http://localhost:5173/`

---

## 🔐 Seguridad implementada

- Autenticación por **JWT**, con renovación automática de token en el frontend.
- **django-axes**: bloqueo de cuentas tras intentos fallidos de inicio de sesión (por usuario e IP).
- **django-simple-history**: auditoría de cambios sobre `Expediente`.
- **Permisos por rol**: `abogado` y `secretario_juridico` solo ven sus expedientes asignados; `administrador` y `socio_director` ven todos.
- Variables sensibles fuera del control de versiones (`.env`, `.gitignore`).

---

## 🛣️ Endpoints principales de la API

| Endpoint | Método | Descripción |
|---|---|---|
| `/api/token/` | POST | Inicio de sesión |
| `/api/token/refresh/` | POST | Renueva el access token |
| `/api/expedientes/` | GET, POST | Listar / crear expedientes |
| `/api/expedientes/{id}/` | GET, PATCH, DELETE | Detalle / editar / eliminar |
| `/api/audiencias/` | GET, POST, PATCH, DELETE | CRUD de audiencias |
| `/api/clientes/` | GET, POST, PATCH, DELETE | CRUD de clientes |
| `/api/facturas/` | GET, POST, PATCH, DELETE | CRUD de facturas |
| `/api/notificaciones/` | GET, PATCH | Notificaciones del usuario |
| `/api/dashboard/stats/` | GET | Estadísticas del panel |
| `/api/perfil/` | GET, PATCH | Perfil del usuario autenticado |

---

## 👥 Roles de usuario

| Rol | Alcance |
|---|---|
| `administrador` | Acceso total al sistema |
| `socio_director` | Acceso total al sistema |
| `abogado` | Solo sus expedientes asignados |
| `secretario_juridico` | Solo expedientes asignados |

---

## 🧩 Estado del proyecto

- [x] Backend: usuarios, expedientes, audiencias, clientes, facturación, notificaciones
- [x] API REST con autenticación JWT
- [x] Seguridad: axes, auditoría, permisos por rol
- [x] Relaciones formales de base de datos (Cliente ↔ Expediente ↔ Factura)
- [x] Frontend: 8 pantallas con CRUD completo, buscadores, reportes analíticos
- [ ] Despliegue en producción
- [ ] Pruebas automatizadas

---

## 👤 Autor

Proyecto desarrollado como parte de las pasantias de Ingeniería de Software.

