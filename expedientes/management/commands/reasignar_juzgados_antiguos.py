from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import ProtectedError

from expedientes.despachos import candidatos_equivalentes
from expedientes.models import Juzgado


class Command(BaseCommand):
    help = (
        "Busca para cada juzgado antiguo (sin código) el despacho equivalente de la Rama Judicial, "
        "pasa a él los expedientes y demás registros, y borra el antiguo. "
        "Sin --aplicar solo muestra el plan."
    )

    def add_arguments(self, parser):
        parser.add_argument("--aplicar", action="store_true", help="Hace los cambios de verdad.")

    def handle(self, *args, aplicar=False, **opciones):
        nuevos = list(Juzgado.objects.filter(codigo__isnull=False))
        viejos = list(Juzgado.objects.filter(codigo__isnull=True).order_by("nombre"))
        if not nuevos:
            self.stdout.write(self.style.ERROR("Primero importe los despachos (comando importar_despachos)."))
            return

        sin_equivalente = []
        for viejo in viejos:
            cand = candidatos_equivalentes(viejo, nuevos)
            if len(cand) != 1:
                motivo = "no se encontró equivalente" if not cand else f"hay {len(cand)} posibles: " + "; ".join(c.etiqueta for c in cand[:3])
                sin_equivalente.append(viejo.nombre)
                self.stdout.write(self.style.WARNING(f"[sin cambios] {viejo.nombre} -> {motivo}"))
                continue
            nuevo = cand[0]
            self.stdout.write(f"{viejo.nombre}  ->  {nuevo.etiqueta}")
            if not aplicar:
                continue
            with transaction.atomic():
                for rel in Juzgado._meta.related_objects:
                    rel.related_model.objects.filter(**{rel.field.name: viejo}).update(**{rel.field.name: nuevo})
                try:
                    viejo.delete()
                except ProtectedError:
                    self.stdout.write(self.style.WARNING(f"   No se pudo borrar {viejo.nombre}: aún tiene registros asociados."))

        if not aplicar:
            self.stdout.write(self.style.SUCCESS("Simulación: no se cambió nada. Use --aplicar para hacerlo."))
        elif sin_equivalente:
            self.stdout.write(self.style.WARNING(f"Quedaron {len(sin_equivalente)} sin equivalente automático."))
        else:
            self.stdout.write(self.style.SUCCESS("Listo: todos los juzgados antiguos fueron reasignados y borrados."))
