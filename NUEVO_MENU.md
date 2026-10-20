# Reestructuración: menú de tres módulos

Este paquete se copia ENCIMA del proyecto (con `mejoras` + `parche1` ya aplicados). Incluye todo lo de `modulos.zip`
(si no lo aplicó, no lo necesita: este paquete lo reemplaza).

## Menú resultante

- **Liquidación** ▸ Laboral · Créditos · Alimentos · Cuotas de administración
- **Vigilancia judicial** (enlaces anclados por proceso + actuaciones y alertas)
- **Administración judicial** ▸
  - Gestión de demanda ▸ A1 Elaboración de demanda · B1 Contestación de demanda
  - Citación de demanda
  - Abogados
  - Audiencias y diligencias judiciales

Todos los grupos se abren y se cierran (recuerdan cómo los dejó). Fuera del menú quedan: Expedientes (se llega desde un
enlace dentro de Vigilancia y Audiencias), Notificaciones (con contador sobre la tarjeta de perfil) y Configuración (tarjeta de perfil).

## Qué se eliminó

Del frontend: Panel, Clientes, Facturación, Reportes y la pantalla Usuarios (ahora es Abogados).
Del backend NO se borró nada: los datos y la API de clientes, facturas y estadísticas siguen ahí (Expedientes y Usuarios dependen de ellos).
Si hace falta recuperar una pantalla: `git checkout main -- frontend/src/pages/Dashboard.jsx` (y la que sea).
