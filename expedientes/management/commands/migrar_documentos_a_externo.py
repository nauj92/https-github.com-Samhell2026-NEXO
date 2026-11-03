from django.core.management.base import BaseCommand, CommandError

from expedientes import almacenamiento
from expedientes.models import DocumentoExpediente


class Command(BaseCommand):
    help = "Pasa los documentos guardados en la base de datos al almacenamiento externo (S3 compatible)."

    def add_arguments(self, parser):
        parser.add_argument("--simular", action="store_true", help="Solo muestra qué se movería, sin cambiar nada.")

    def handle(self, *args, **opciones):
        if not almacenamiento.configurado():
            raise CommandError("Defina DOCUMENTOS_BUCKET (y las credenciales) antes de migrar los documentos.")
        pendientes = DocumentoExpediente.objects.filter(ruta_externa="")
        movidos = fallidos = 0
        for doc in pendientes.iterator():
            if opciones["simular"]:
                self.stdout.write(f"[simulación] {doc.expediente_id}/{doc.nombre} ({doc.tamano} bytes)")
                movidos += 1
                continue
            try:
                ruta = almacenamiento.guardar(doc.expediente_id, doc.nombre, bytes(doc.contenido), doc.tipo_contenido)
            except almacenamiento.ErrorAlmacenamiento as exc:
                fallidos += 1
                self.stderr.write(f"No se pudo mover {doc.pk} ({doc.nombre}): {exc}")
                continue
            doc.ruta_externa = ruta
            doc.contenido = b""
            doc.save(update_fields=["ruta_externa", "contenido"])
            movidos += 1
        verbo = "Se moverían" if opciones["simular"] else "Movidos"
        self.stdout.write(f"{verbo}: {movidos}. Fallidos: {fallidos}.")
