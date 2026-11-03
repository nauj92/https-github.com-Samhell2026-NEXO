from datetime import date

from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from .plazos import (
    ADVERTENCIA,
    ADVERTENCIA_VACANCIA,
    _con_vacancia,
    dias_de_vacancia_en_rango,
    festivos_en_rango,
    sumar_dias_habiles,
)


class CalcularPlazoView(APIView):
    """GET /api/plazos/calcular/?dias=10[&fecha_inicio=2026-03-20][&vacancia=true]

    Calcula la fecha de vencimiento de un término en días hábiles. Con `vacancia=true` descuenta además la
    vacancia judicial (Semana Santa y del 20 de diciembre al 10 de enero); `vacancia=false` la ignora; si no se
    indica, se usa la configuración del sistema.
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

        texto_vacancia = request.query_params.get("vacancia")
        if texto_vacancia is None or texto_vacancia == "":
            vacancia = _con_vacancia(None)
        elif texto_vacancia.lower() in ("1", "true", "si", "sí"):
            vacancia = True
        elif texto_vacancia.lower() in ("0", "false", "no"):
            vacancia = False
        else:
            return Response({"detail": "El parámetro vacancia debe ser true o false."}, status=400)

        vence = sumar_dias_habiles(inicio, dias, vacancia=vacancia)
        return Response(
            {
                "fecha_inicio": inicio.isoformat(),
                "dias_habiles": dias,
                "fecha_vencimiento": vence.isoformat(),
                "festivos_en_el_rango": [
                    {"fecha": f.isoformat(), "nombre": n} for f, n in festivos_en_rango(inicio, vence)
                ],
                "con_vacancia_judicial": vacancia,
                "dias_de_vacancia_descontados": dias_de_vacancia_en_rango(inicio, vence) if vacancia else 0,
                "advertencia": ADVERTENCIA_VACANCIA if vacancia else ADVERTENCIA,
            }
        )
