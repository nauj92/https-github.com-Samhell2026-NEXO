from django.core.management.base import BaseCommand, CommandError

from expedientes.despachos import interpretar_despacho
from expedientes.models import Juzgado


class Command(BaseCommand):
    help = (
        "Importa despachos de la Rama Judicial desde un archivo de texto con una línea por despacho "
        "en el formato «110013109032 - JUZGADO 032 PENAL DEL CIRCUITO …». Es idempotente: "
        "actualiza por código y no duplica."
    )

    def add_arguments(self, parser):
        parser.add_argument("archivo", help="Ruta del .txt (UTF-8).")
        parser.add_argument("--simular", action="store_true", help="Solo muestra qué haría, sin guardar.")

    def handle(self, *args, archivo, simular=False, **opciones):
        try:
            with open(archivo, encoding="utf-8-sig") as f:
                lineas = f.read().splitlines()
        except OSError as e:
            raise CommandError(f"No se pudo leer el archivo: {e}")

        creados = actualizados = omitidos = 0
        for linea in lineas:
            if not linea.strip():
                continue
            datos = interpretar_despacho(linea)
            if datos is None:
                omitidos += 1
                continue
            codigo = datos.pop("codigo")
            if simular:
                existe = Juzgado.objects.filter(codigo=codigo).exists()
                creados += 0 if existe else 1
                actualizados += 1 if existe else 0
                continue
            _, creado = Juzgado.objects.update_or_create(codigo=codigo, defaults=datos)
            creados += creado
            actualizados += not creado
        prefijo = "(Simulación) " if simular else ""
        self.stdout.write(self.style.SUCCESS(
            f"{prefijo}Despachos creados: {creados}, actualizados: {actualizados}, líneas omitidas: {omitidos}."
        ))
