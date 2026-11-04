# Guía de validación con usuarios del oficio

Objetivo: comprobar con abogados y secretarios de juzgado que ACOPROHO sirve para su trabajo real, antes de dar el sistema por terminado.

## 1. Participantes

| Perfil | Cantidad sugerida |
|---|---|
| Abogado litigante | 2 a 3 |
| Secretario(a) o escribiente de juzgado | 1 a 2 |
| Socio director o administrador del despacho | 1 |

Con 5 a 6 personas se detecta la gran mayoría de los problemas de uso.

## 2. Preparación (30 minutos antes)

1. Entre al ambiente en línea y verifique que responde (el plan gratuito de Render puede tardar hasta un minuto en despertar).
2. Como administrador, cree una cuenta por participante (menú **Abogados y usuarios**). Cada persona recibirá su correo y deberá cambiar la contraseña y autorizar el uso de sus datos: eso también forma parte de la prueba.
3. Use datos ficticios. No cargue procesos ni clientes reales hasta tener aprobación del despacho.
4. Prepare una copia de la hoja de observación (sección 5) por participante.

## 3. Desarrollo de la sesión (45 minutos por persona)

1. Explique en 2 minutos para qué sirve el sistema. No muestre cómo se usa.
2. Pida que realice las tareas de la sección 4, pensando en voz alta.
3. Observe sin ayudar. Anote dónde duda, se equivoca o pregunta.
4. Al final aplique el cuestionario de la sección 6 y pregunte qué cambiaría primero.

## 4. Tareas

| N.º | Tarea | Éxito si… |
|---|---|---|
| 1 | Iniciar sesión por primera vez: cambiar la contraseña y autorizar los datos | Llega al Dashboard sin ayuda |
| 2 | Registrar un cliente nuevo | El cliente aparece en la lista |
| 3 | Crear una demanda (A1) para ese cliente, eligiendo despacho y clase de proceso | Guarda y ve el verificador de requisitos del art. 82 |
| 4 | Revisar el borrador de la demanda y corregir un dato | Entiende qué falta y lo corrige |
| 5 | Crear una contestación (B1) con fecha de notificación | Ve la fecha límite de vencimiento y es la que esperaba |
| 6 | Registrar un expediente con radicado de 23 dígitos y adjuntar un documento | El documento se puede descargar |
| 7 | Programar una audiencia y encontrarla en el Dashboard | La ve en "Audiencias y diligencias" |
| 8 | Calcular un término en días hábiles que cruce un festivo | Confirma que la fecha es correcta |
| 9 | (Solo administrador) Crear un usuario y verificar el estado "Primer ingreso" | Entiende si la persona ya completó su ingreso |

## 5. Hoja de observación (una por persona)

| Tarea | ¿La completó? (Sí / Con ayuda / No) | Tiempo | Dónde dudó o se equivocó | Comentario textual |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |
| 6 | | | | |
| 7 | | | | |
| 8 | | | | |
| 9 | | | | |

## 6. Cuestionario (1 = totalmente en desacuerdo, 5 = totalmente de acuerdo)

1. Me gustaría usar este sistema con frecuencia en mi trabajo.
2. El sistema me pareció innecesariamente complejo.
3. El sistema fue fácil de usar.
4. Necesitaría ayuda de alguien para poder usarlo.
5. Las funciones están bien integradas entre sí.
6. Encontré demasiadas inconsistencias.
7. La mayoría de mis colegas aprendería a usarlo rápido.
8. El sistema me pareció incómodo de usar.
9. Me sentí seguro(a) usándolo.
10. Tuve que aprender muchas cosas antes de poder usarlo.

Puntaje (escala SUS): para las preguntas impares reste 1 a la respuesta; para las pares, reste la respuesta a 5. Sume los 10 valores y multiplique por 2,5. Más de 68 se considera aceptable; más de 80, muy bueno.

Preguntas abiertas:
- ¿Qué fue lo más útil?
- ¿Qué fue lo más confuso o lo que le faltó?
- ¿Reemplazaría alguna herramienta que usa hoy por esta? ¿Cuál?
- ¿Falta algún formato, cálculo o término propio de su jurisdicción?

## 7. Registro de hallazgos

| N.º | Hallazgo | Gravedad (Alta / Media / Baja) | Cuántas personas lo sufrieron | Acción propuesta | Estado |
|---|---|---|---|---|---|
| 1 | | | | | |

Criterio de gravedad: **Alta** impide terminar la tarea; **Media** la retrasa o genera error; **Baja** es una molestia.

## 8. Cierre

1. Consolide los puntajes SUS y los hallazgos en una sola tabla.
2. Corrija primero los hallazgos de gravedad alta que afectaron a más de una persona.
3. Repita la sesión con 2 o 3 personas para confirmar las correcciones.
4. Cuando el puntaje SUS promedio sea mayor a 68 y no queden hallazgos de gravedad alta, marque en el README: `[x] Validación con usuarios del oficio`.

## 9. Pendientes que conviene confirmar con el despacho

- Texto de la autorización de tratamiento de datos (lo debe revisar el asesor jurídico).
- Si los términos del despacho deben descontar la vacancia judicial (`PLAZOS_CON_VACANCIA`).
- Qué debe poder ver el rol Cliente (hoy solo su perfil).
