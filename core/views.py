from datetime import date

from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from .plazos import ADVERTENCIA, festivos_en_rango, sumar_dias_habiles


class CalcularPlazoView(APIView):
    """GET /api/plazos/calcular/?dias=10[&fecha_inicio=2026-03-20]

    Calcula la fecha de vencimiento de un término en días hábiles.
    """

    def get(self, request):
        try:
            dias = int(request.query_params.get("dias", ""))
        except ValueError:
            return Response({"detail": "Indique los días hábiles como un número entero."}, status=400)
        if not 1 <= dias <= 365:
            return Response({"detail": "Los días hábiles deben estar entre 1 y 365."}, status=400)

        texto = request.query_params.get("fecha_inicio")
        if texto:
            try:
                inicio = date.fromisoformat(texto)
            except ValueError:
                return Response({"detail": "La fecha de inicio debe tener el formato AAAA-MM-DD."}, status=400)
        else:
            inicio = timezone.localdate()

        vence = sumar_dias_habiles(inicio, dias)
        return Response(
            {
                "fecha_inicio": inicio.isoformat(),
                "dias_habiles": dias,
                "fecha_vencimiento": vence.isoformat(),
                "festivos_en_el_rango": [
                    {"fecha": f.isoformat(), "nombre": n} for f, n in festivos_en_rango(inicio, vence)
                ],
                "advertencia": ADVERTENCIA,
            }
        )
