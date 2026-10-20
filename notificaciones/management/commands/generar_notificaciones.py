from django.core.management.base import BaseCommand

from notificaciones.servicios import actualizar_facturas_vencidas, generar_para_todos


class Command(BaseCommand):
    help = "Genera las notificaciones automáticas (audiencias, plazos y facturas) de todos los usuarios."

    def handle(self, *args, **options):
        vencidas = actualizar_facturas_vencidas()
        creadas = generar_para_todos()
        self.stdout.write(self.style.SUCCESS(f"Notificaciones creadas: {creadas}. Facturas marcadas vencidas: {vencidas}."))
