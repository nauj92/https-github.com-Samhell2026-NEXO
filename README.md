# ⚖️ ERP — Sistema de Gestión Judicial (NEXO / ERP Operador Judicial)

Sistema de administración de gestión jurídica para despachos de abogados. Permite gestionar expedientes, audiencias, clientes, facturación y notificaciones, con control de acceso por roles y trazabilidad de cambios.

Proyecto desarrollado en el marco de las **Pasantias de Ingeniería de Software**.

---

## 📋 Descripción general

El sistema ERP centraliza el flujo de trabajo de un despacho jurídico:

- **Expedientes**: registro y seguimiento de casos judiciales, con etapas del proceso (línea de tiempo).
- **Audiencias**: agenda de audiencias vinculadas a cada expediente.
- **Clientes**: base de datos de clientes del despacho, relacionada formalmente con expedientes y facturas.
- **Facturación**: control de facturas emitidas, su estado y vencimiento.
- **Notificaciones**: alertas internas generadas automáticamente (audiencias próximas, plazos próximos o vencidos, facturas vencidas), sin duplicados.
- **Plazos procesales**: cálculo de fechas límite en días hábiles con los festivos de Colombia.
- **Documentos e historial**: archivos adjuntos por expediente y registro visible de quién cambió qué y cuándo.
- **Menú desplegable con tres módulos**: Liquidación, Vigilancia judicial y Administración judicial.
- **Liquidación**: laboral, créditos, alimentos y cuotas de administración, con detalle del cálculo, supuestos, impresión y registro de lo guardado.
- **Vigilancia judicial**: seguimiento interno de procesos con enlaces anclados por proceso (consulta de procesos, estados, expediente digital), registro de actuaciones y alerta cuando pasan días sin movimiento.
- **Administración judicial**: Gestión de demanda (A1 Elaboración de demanda con borrador editable; B1 Contestación de demanda con vencimiento en días hábiles y borrador), Citación de demanda (art. 291 y 292 CGP), Abogados (gestión de usuarios) y Audiencias y diligencias judiciales.
- **Gestión de usuarios**: alta, edición, activación y desbloqueo desde la aplicación, y recuperación de contraseña por correo.
- **Notificaciones**: pantalla propia con contador en el menú.

> Las pantallas de Panel, Clientes, Facturación y Reportes fueron retiradas del frontend en la reestructuración del menú; el backend y los datos de esas áreas se conservan (la API sigue disponible).

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
├── liquidaciones/ # Liquidaciones guardadas y API de cálculo
├── vigilancia/ # Vigilancia judicial y actuaciones
├── demandas/ # Gestión de demandas
├── core/ # Permisos por rol, cálculo de plazos (días hábiles), comando cargar_demo
├── frontend/ # Aplicación React (interfaz de usuario)
│ ├── src/
│ │ ├── pages/ # Liquidacion, Vigilancia, Demandas (A1), Contestaciones (B1), Citaciones, Abogados, Audiencias, Notificaciones, Expedientes, Login, etc.
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
- **DocumentoExpediente** — archivos adjuntos de un Expediente (máx. 5 MB, guardados en la base de datos).
- **Audiencia** — audiencia o diligencia judicial (`tipo`, `clase`) relacionada con un Expediente.
- **Cliente** — relacionado formalmente con Expediente y Factura.
- **Factura** — relacionada opcionalmente con Expediente, y con Cliente.
- **Notificacion** — relacionada con Usuario; el campo `clave` evita duplicados.
- **Liquidacion** — liquidación guardada (laboral, crédito, alimentos o cuotas): datos de entrada y resultado en JSON, total, expediente opcional y quién la creó.
- **Vigilancia** — proceso vigilado (uno por Expediente), con los días de alerta sin movimiento.
- **ActuacionVigilancia** — actuaciones que se registran de un proceso vigilado.
- **EnlaceVigilancia** — enlaces anclados a un proceso vigilado (título, dirección http/https y nota).
- **Demanda** — A1: demanda en elaboración o radicada, con estados, fechas de radicación, inadmisión y admisión, y borrador editable.
- **ContestacionDemanda** — B1: contestación con fecha de notificación, término en días hábiles, excepciones, pruebas y borrador.
- **Citacion** — citación (art. 291 CGP) o aviso (art. 292 CGP) con mensajería, guía y fechas de envío, entrega y notificación.

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
    EXPEDIENTE ||--o{ DOCUMENTOEXPEDIENTE : "adjunta"
    EXPEDIENTE ||--o| VIGILANCIA : "se vigila"
    EXPEDIENTE ||--o{ LIQUIDACION : "se liquida"
    EXPEDIENTE ||--o{ DEMANDA : "origina"
    EXPEDIENTE ||--o{ CONTESTACIONDEMANDA : "origina"
    EXPEDIENTE ||--o{ CITACION : "origina"
    VIGILANCIA ||--o{ ACTUACIONVIGILANCIA : "registra"
    VIGILANCIA ||--o{ ENLACEVIGILANCIA : "ancla"
    DEMANDA ||--o{ CITACION : "notifica"
    CLIENTE ||--o{ DEMANDA : "demanda"
    CLIENTE ||--o{ CONTESTACIONDEMANDA : "contesta"
    USUARIO ||--o{ DEMANDA : "abogado_responsable"
    USUARIO ||--o{ CONTESTACIONDEMANDA : "abogado_responsable"
    USUARIO ||--o{ CITACION : "abogado_responsable"
    USUARIO ||--o{ LIQUIDACION : "crea"

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
        string tipo
        string clase
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
        date fecha_pago
    }

    NOTIFICACION {
        int id PK
        int usuario_id FK
        string tipo
        string mensaje
        boolean leida
        datetime creada_en
    }

    DOCUMENTOEXPEDIENTE {
        int id PK
        int expediente_id FK
        string nombre
        string tipo_contenido
        int tamano
        binary contenido
        int subido_por_id FK
        datetime subido_en
    }

    LIQUIDACION {
        int id PK
        string tipo
        string referencia
        int expediente_id FK
        json datos
        json resultado
        decimal total
        int creado_por_id FK
        datetime creado_en
    }

    VIGILANCIA {
        int id PK
        int expediente_id FK
        boolean activa
        int dias_alerta
        string observaciones
        datetime creado_en
    }

    ACTUACIONVIGILANCIA {
        int id PK
        int vigilancia_id FK
        date fecha
        string descripcion
        int registrada_por_id FK
    }

    ENLACEVIGILANCIA {
        int id PK
        int vigilancia_id FK
        string titulo
        string url
        string nota
        int creado_por_id FK
    }

    DEMANDA {
        int id PK
        string clase_proceso
        int cliente_id FK
        int expediente_id FK
        int juzgado_id FK
        string demandante
        string demandado
        decimal cuantia
        string estado
        date fecha_radicacion
        date fecha_inadmision
        date fecha_admision
        int abogado_responsable_id FK
        string borrador
    }

    CONTESTACIONDEMANDA {
        int id PK
        string clase_proceso
        string demandante
        string demandado
        int cliente_id FK
        int expediente_id FK
        date fecha_notificacion
        int dias_termino
        string estado
        date fecha_presentacion
        int abogado_responsable_id FK
        string borrador
    }

    CITACION {
        int id PK
        int demanda_id FK
        int expediente_id FK
        string destinatario
        string tipo
        string ubicacion
        string estado
        date fecha_envio
        string guia
        date fecha_entrega
        date fecha_notificacion
        int abogado_responsable_id FK
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
- **django-simple-history**: auditoría de cambios sobre `Expediente`, visible en la pantalla del expediente.
- **Permisos por rol**: `abogado` y `secretario_juridico` solo ven sus expedientes asignados; `administrador` y `socio_director` ven todos.
- **Recuperación de contraseña** con enlace de un solo uso y vigencia de 1 hora; no revela si el correo existe y está limitada a 30 solicitudes por hora.
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
| `/api/plazos/calcular/?dias=N` | GET | Fecha límite en N días hábiles (festivos de Colombia) |
| `/api/expedientes/{id}/historial/` | GET | Historial de cambios del expediente |
| `/api/expedientes/{id}/documentos/` | GET, POST | Listar / adjuntar documentos |
| `/api/expedientes/{id}/documento/{doc_id}/` | GET, DELETE | Descargar / eliminar documento |
| `/api/gestion-usuarios/` | GET, POST, PATCH | Gestión de usuarios (administrador y socio director) |
| `/api/gestion-usuarios/{id}/desbloquear/` | POST | Reinicia el bloqueo por intentos fallidos |
| `/api/liquidaciones/calcular/` | POST | Calcula una liquidación (laboral, credito, alimentos o cuotas) sin guardar |
| `/api/liquidaciones/` | GET, POST, DELETE | Liquidaciones guardadas |
| `/api/vigilancia/` | GET, POST, PATCH, DELETE | Procesos en vigilancia |
| `/api/vigilancia/{id}/actuaciones/` | GET, POST | Actuaciones del proceso vigilado |
| `/api/vigilancia/{id}/enlaces/` | GET, POST | Enlaces anclados al proceso vigilado |
| `/api/vigilancia/{id}/enlace/{enlace_id}/` | DELETE | Quita un enlace anclado |
| `/api/demandas/` | GET, POST, PATCH, DELETE | A1 · Elaboración de demanda |
| `/api/demandas/{id}/generar-borrador/` | GET | Borrador de la demanda desde plantilla (no lo guarda) |
| `/api/contestaciones/` | GET, POST, PATCH, DELETE | B1 · Contestación de demanda |
| `/api/contestaciones/{id}/generar-borrador/` | GET | Borrador de la contestación |
| `/api/citaciones/` | GET, POST, PATCH, DELETE | Citaciones (art. 291) y avisos (art. 292) |
| `/api/password-reset/` | POST | Solicita el enlace de recuperación |
| `/api/password-reset/confirmar/` | POST | Establece la contraseña nueva |

---

## ⚖️ Reglas de negocio

- **Radicado**: 23 dígitos (ciudad DANE 5 + corporación 2 + especialidad 2 + despacho 3 + año 4 + consecutivo 5 + recurso 2). Se rechaza cualquier otro formato.
- **Plazos**: los días hábiles excluyen sábados, domingos y festivos de Colombia (Ley Emiliani y Semana Santa); el conteo inicia el día hábil siguiente. No considera vacancia judicial ni suspensiones de términos.
- **Notificaciones automáticas**: audiencias y plazos en los próximos 3 días, plazos vencidos y facturas vencidas o por vencer (estas últimas solo para administrador y socio director).
- **Liquidaciones**: las tasas (interés bancario corriente, usura), el salario mínimo y el auxilio de transporte se digitan según la certificación vigente. Los abonos de un crédito se imputan primero a intereses y luego a capital. La liquidación laboral no incluye sanción moratoria, aportes ni retención.
- **Alimentos**: la cuota se incrementa cada 1 de enero con el porcentaje digitado; el interés es opcional (tasa digitada); los abonos se restan del total. Verifique los valores con la sentencia o el acuerdo.
- **Demandas (A1)**: una demanda inadmitida tiene 5 días hábiles para subsanarse (art. 90 CGP); el sistema calcula el vencimiento y avisa. El borrador es un punto de partida desde plantilla, que el abogado debe revisar.
- **Contestación (B1)**: 20 días hábiles desde la notificación por defecto (editable entre 1 y 90); se marca extemporánea si se presenta después del vencimiento.
- **Citación**: el plazo para comparecer cuenta 5, 10 o 30 días hábiles desde la entrega según el demandado esté en el mismo municipio, en otro o en el exterior; el aviso se considera surtido el día hábil siguiente a su entrega (supuesto: verifique con el despacho).
- **Vigilancia**: se alerta cuando un proceso vigilado supera los días configurados sin actuaciones registradas; los enlaces solo admiten http/https; no se conecta a la Rama Judicial.
- **Alcance por rol**: abogados y secretarios ven demandas, contestaciones y citaciones propias o de sus expedientes; administrador y socio director ven todas.
- **Ingresos del mes**: suma de facturas pagadas según su fecha de pago.

---

## 🧪 Pruebas y datos de demostración

```bash
python manage.py test                 # pruebas automatizadas del backend
python manage.py cargar_demo          # carga casos de ejemplo (idempotente)
python manage.py generar_notificaciones
```

Variables opcionales: `CARGAR_DEMO=1` (carga la demo en el despliegue), `DEMO_PASSWORD` (crea usuarios demo de cada rol), `RESEND_API_KEY` y `DEFAULT_FROM_EMAIL` (envío real de correos), `FRONTEND_URL` (enlace de recuperación).

---

## 👥 Roles de usuario

| Rol | Alcance |
|---|---|
| `administrador` | Acceso total al sistema |
| `socio_director` | Acceso total al sistema |
| `abogado` | Solo sus expedientes asignados |
| `secretario_juridico` | Solo expedientes asignados |

---

## 🌐 Despliegue en línea

La aplicación está desplegada en [Render](https://render.com) (plan gratuito) como ambiente de demostración.

| Componente | Dirección |
|---|---|
| Aplicación (frontend) | https://erp-frontend-wo14.onrender.com |
| API REST (backend) | https://erp-backend-dxe7.onrender.com |
| Panel de administración | https://erp-backend-dxe7.onrender.com/admin/ |

> El backend se suspende tras 15 minutos sin uso y la primera petición puede tardar cerca de un minuto. La base de datos PostgreSQL gratuita expira a los 30 días de su creación.

**Backend (Web Service, Python 3)**
- Build Command: `./build.sh` (instala dependencias, `collectstatic`, `migrate` y crea el superusuario si no existe)
- Start Command: `gunicorn config.wsgi:application`
- Variables de entorno: `DJANGO_SETTINGS_MODULE=config.settings.prod`, `SECRET_KEY`, `DATABASE_URL`, `DEBUG`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL`

**Frontend (Static Site)**
- Root Directory: `frontend`
- Build Command: `npm install && npm run build`
- Publish Directory: `dist`
- Variable de entorno: `VITE_API_URL=https://erp-backend-dxe7.onrender.com/api`

## 🧩 Estado del proyecto

- [x] Backend: usuarios, expedientes, audiencias, clientes, facturación, notificaciones
- [x] API REST con autenticación JWT
- [x] Seguridad: axes, auditoría, permisos por rol
- [x] Relaciones formales de base de datos (Cliente ↔ Expediente ↔ Factura)
- [x] Frontend: pantallas de los tres módulos del menú, Expedientes (acceso desde los módulos), Notificaciones y Configuración
- [x] Despliegue en línea (ambiente de demostración en Render) 
- [x] Radicado de 23 dígitos, cálculo de plazos en días hábiles, notificaciones automáticas
- [x] Documentos adjuntos, historial visible, gestión de usuarios y recuperación de contraseña
- [x] Pruebas automatizadas del backend
- [x] Menú desplegable: Liquidación (laboral, créditos, alimentos, cuotas), Vigilancia judicial con enlaces y Administración judicial (A1, B1, citación, abogados, audiencias y diligencias)
- [ ] Validación con usuarios del oficio (abogados / secretarios de juzgado)
- [ ] Pruebas automatizadas del frontend
- [ ] Almacenamiento externo de documentos y vacancia judicial en el cálculo de plazos

---

## 👤 Autor

Proyecto desarrollado como parte de las pasantias de Ingeniería de Software.

