from datetime import date

from django.test import SimpleTestCase

from core.liquidaciones import (
    ErrorLiquidacion,
    dias_360,
    liquidar_credito,
    liquidar_alimentos,
    liquidar_cuotas_administracion,
    liquidar_laboral,
    tasa_mensual,
)


class DiasComercialesTests(SimpleTestCase):
    def test_anio_completo_son_360_dias(self):
        self.assertEqual(dias_360(date(2026, 1, 1), date(2026, 12, 31)), 360)

    def test_febrero_cuenta_como_treinta(self):
        self.assertEqual(dias_360(date(2026, 1, 1), date(2026, 2, 28)), 60)

    def test_un_dia(self):
        self.assertEqual(dias_360(date(2026, 5, 10), date(2026, 5, 10)), 1)

    def test_fin_antes_de_inicio_da_cero(self):
        self.assertEqual(dias_360(date(2026, 5, 10), date(2026, 5, 9)), 0)

    def test_tasa_mensual_equivalente(self):
        # 30% EA equivale a ~2.2104% mensual
        self.assertAlmostEqual(float(tasa_mensual(30)) * 100, 2.2104, places=3)
        self.assertEqual(float(tasa_mensual(0)), 0.0)


class LiquidacionLaboralTests(SimpleTestCase):
    def conceptos(self, r):
        return {c["concepto"]: c for c in r["conceptos"]}

    def test_liquidacion_con_indemnizacion_indefinido(self):
        r = liquidar_laboral(
            2_000_000, date(2023, 3, 1), date(2026, 10, 15), auxilio_transporte=200_000,
            indemnizacion=True, salario_minimo=1_750_905,
        )
        c = self.conceptos(r)
        self.assertEqual(c["Cesantías"]["valor"], 1_741_667)
        self.assertEqual(c["Cesantías"]["dias"], 285)
        self.assertEqual(c["Intereses sobre cesantías"]["valor"], 165_458)
        self.assertEqual(c["Prima de servicios"]["valor"], 641_667)
        self.assertEqual(c["Vacaciones"]["valor"], 3_625_000)
        indem = [v for k, v in c.items() if k.startswith("Indemnización")][0]
        self.assertEqual(indem["dias"], 82.5)  # 30 + 20 × 2.625 años
        self.assertEqual(indem["valor"], 5_500_000)
        self.assertEqual(r["total"], 11_673_792)

    def test_indemnizacion_menos_de_un_anio_son_30_dias(self):
        r = liquidar_laboral(1_500_000, date(2026, 7, 1), date(2026, 9, 30), indemnizacion=True, salario_minimo=1_500_000)
        indem = [c for c in r["conceptos"] if c["concepto"].startswith("Indemnización")][0]
        self.assertEqual(indem["valor"], 1_500_000)

    def test_indemnizacion_diez_o_mas_salarios_minimos(self):
        r = liquidar_laboral(
            20_000_000, date(2025, 10, 16), date(2026, 10, 15), indemnizacion=True, salario_minimo=1_500_000
        )
        indem = [c for c in r["conceptos"] if c["concepto"].startswith("Indemnización")][0]
        self.assertEqual(indem["valor"], 13_333_333)  # 20 días de salario

    def test_indemnizacion_termino_fijo(self):
        r = liquidar_laboral(
            3_000_000, date(2026, 1, 1), date(2026, 10, 15), indemnizacion=True,
            tipo_contrato="fijo", fecha_fin_pactada=date(2026, 12, 31),
        )
        indem = [c for c in r["conceptos"] if c["concepto"].startswith("Indemnización")][0]
        self.assertEqual(indem["dias"], 77)
        self.assertEqual(indem["valor"], 7_700_000)

    def test_deducciones_y_salarios_pendientes(self):
        r = liquidar_laboral(3_000_000, date(2026, 1, 1), date(2026, 3, 31), salarios_pendientes_dias=10, deducciones=100_000)
        c = self.conceptos(r)
        self.assertEqual(c["Salarios pendientes"]["valor"], 1_000_000)
        self.assertEqual(r["deducciones"], 100_000)
        self.assertEqual(r["total"], r["subtotal"] - 100_000)

    def test_vacaciones_ya_disfrutadas_se_descuentan(self):
        sin = liquidar_laboral(3_000_000, date(2025, 1, 1), date(2025, 12, 31))
        con = liquidar_laboral(3_000_000, date(2025, 1, 1), date(2025, 12, 31), dias_vacaciones_disfrutados=15)
        self.assertEqual(self.conceptos(sin)["Vacaciones"]["valor"], 1_500_000)  # 15 días de descanso
        self.assertEqual(self.conceptos(con)["Vacaciones"]["valor"], 0)

    def test_errores(self):
        with self.assertRaises(ErrorLiquidacion):
            liquidar_laboral(2_000_000, date(2026, 5, 1), date(2026, 4, 1))
        with self.assertRaises(ErrorLiquidacion):
            liquidar_laboral(2_000_000, date(2025, 1, 1), date(2026, 4, 1), indemnizacion=True)  # falta SMMLV
        with self.assertRaises(ErrorLiquidacion):
            liquidar_laboral(2_000_000, date(2025, 1, 1), date(2026, 4, 1), indemnizacion=True, tipo_contrato="fijo")


class LiquidacionCreditoTests(SimpleTestCase):
    def test_un_mes_sin_abonos(self):
        r = liquidar_credito(1_000_000, date(2026, 1, 1), date(2026, 1, 30), tasa_ea=30)
        self.assertEqual(len(r["tramos"]), 1)
        self.assertEqual(r["tramos"][0]["dias"], 30)
        self.assertAlmostEqual(r["intereses_causados"], 22_104, delta=5)
        self.assertEqual(r["total"], r["capital_pendiente"] + r["intereses_pendientes"])

    def test_abono_se_imputa_primero_a_intereses(self):
        r = liquidar_credito(
            10_000_000, date(2026, 1, 1), date(2026, 6, 30), tasa_ea=30,
            abonos=[{"fecha": date(2026, 3, 31), "valor": 1_000_000}],
        )
        self.assertEqual(len(r["tramos"]), 2)
        self.assertEqual(r["abonos"][0]["a_intereses"], 663_134)
        self.assertEqual(r["abonos"][0]["a_capital"], 336_866)
        self.assertEqual(r["tramos"][1]["capital"], 9_663_134)
        self.assertEqual(r["intereses_pendientes"], 647_915)
        self.assertEqual(r["total"], 10_311_048)

    def test_periodos_con_distinta_tasa(self):
        periodos = [
            {"desde": date(2026, 1, 1), "hasta": date(2026, 1, 31), "tasa_ea": 30},
            {"desde": date(2026, 2, 1), "hasta": date(2026, 3, 31), "tasa_ea": 20},
        ]
        r = liquidar_credito(5_000_000, date(2026, 1, 1), date(2026, 3, 31), periodos=periodos, costas=250_000)
        self.assertEqual([t["tasa_ea"] for t in r["tramos"]], [30.0, 20.0])
        self.assertEqual(sum(t["dias"] for t in r["tramos"]), 90)
        self.assertEqual(r["costas"], 250_000)
        self.assertEqual(r["total"], 5_000_000 + r["intereses_pendientes"] + 250_000)

    def test_errores(self):
        with self.assertRaises(ErrorLiquidacion):
            liquidar_credito(1_000_000, date(2026, 1, 1), date(2026, 2, 1))  # sin tasa
        with self.assertRaises(ErrorLiquidacion):
            liquidar_credito(1_000_000, date(2026, 2, 1), date(2026, 1, 1), tasa_ea=30)
        huecos = [
            {"desde": date(2026, 1, 1), "hasta": date(2026, 1, 15), "tasa_ea": 30},
            {"desde": date(2026, 1, 20), "hasta": date(2026, 2, 28), "tasa_ea": 20},
        ]
        with self.assertRaises(ErrorLiquidacion):
            liquidar_credito(1_000_000, date(2026, 1, 1), date(2026, 2, 28), periodos=huecos)
        with self.assertRaises(ErrorLiquidacion):
            liquidar_credito(1_000_000, date(2026, 1, 1), date(2026, 2, 28), tasa_ea=30, abonos=[{"fecha": date(2026, 3, 1), "valor": 10}])
        with self.assertRaises(ErrorLiquidacion):
            liquidar_credito(
                1_000, date(2026, 1, 1), date(2026, 2, 28), tasa_ea=30,
                abonos=[{"fecha": date(2026, 1, 10), "valor": 99_999_999}],
            )


class LiquidacionCuotasTests(SimpleTestCase):
    def test_seis_cuotas(self):
        r = liquidar_cuotas_administracion(300_000, date(2026, 1, 1), date(2026, 6, 1), 5, date(2026, 6, 30), 30)
        self.assertEqual(len(r["filas"]), 6)
        self.assertEqual(r["capital"], 1_800_000)
        self.assertEqual(r["intereses"], 133_731)
        self.assertEqual(r["total"], 1_933_731)
        self.assertEqual(r["filas"][0]["dias_mora"], 176)  # del 5 de enero al 30 de junio

    def test_solo_incluye_cuotas_vencidas_a_la_fecha_de_corte(self):
        r = liquidar_cuotas_administracion(300_000, date(2026, 1, 1), date(2026, 6, 1), 5, date(2026, 3, 10), 30)
        self.assertEqual(len(r["filas"]), 3)

    def test_extraordinaria_y_abonos(self):
        r = liquidar_cuotas_administracion(
            300_000, date(2026, 1, 1), date(2026, 1, 1), 5, date(2026, 2, 5), 0,
            extraordinarias=[{"concepto": "Fachada", "fecha_vencimiento": date(2026, 1, 20), "valor": 500_000}],
            abonos_total=100_000,
        )
        self.assertEqual(r["capital"], 800_000)
        self.assertEqual(r["intereses"], 0)
        self.assertEqual(r["total"], 700_000)

    def test_ninguna_vencida_es_error(self):
        with self.assertRaises(ErrorLiquidacion):
            liquidar_cuotas_administracion(300_000, date(2026, 5, 1), date(2026, 6, 1), 5, date(2026, 4, 1), 30)


class LiquidacionAlimentosTests(SimpleTestCase):
    def test_cuotas_sin_incremento_ni_interes(self):
        r = liquidar_alimentos(500_000, date(2026, 1, 1), date(2026, 6, 1), 5, date(2026, 6, 30))
        self.assertEqual(len(r["filas"]), 6)
        self.assertEqual(r["capital"], 3_000_000)
        self.assertEqual(r["intereses"], 0)
        self.assertEqual(r["total"], 3_000_000)

    def test_incremento_anual_se_aplica_cada_enero(self):
        r = liquidar_alimentos(1_000_000, date(2025, 11, 1), date(2026, 2, 1), 5, date(2026, 3, 1), incremento_anual=10)
        valores = [f["valor"] for f in r["filas"]]
        self.assertEqual(valores, [1_000_000, 1_000_000, 1_100_000, 1_100_000])

    def test_interes_y_adicionales_y_abonos(self):
        r = liquidar_alimentos(
            300_000, date(2026, 1, 1), date(2026, 1, 1), 5, date(2026, 2, 5), tasa_ea=6,
            adicionales=[{"concepto": "Prima de junio", "fecha_vencimiento": date(2026, 1, 20), "valor": 300_000}],
            abonos_total=100_000,
        )
        self.assertEqual(r["capital"], 600_000)
        self.assertGreater(r["intereses"], 0)
        self.assertEqual(r["total"], r["capital"] + r["intereses"] - 100_000)

    def test_errores(self):
        with self.assertRaises(ErrorLiquidacion):
            liquidar_alimentos(500_000, date(2026, 5, 1), date(2026, 6, 1), 5, date(2026, 4, 1))
        with self.assertRaises(ErrorLiquidacion):
            liquidar_alimentos(500_000, date(2026, 6, 1), date(2026, 5, 1), 5, date(2026, 7, 1))
