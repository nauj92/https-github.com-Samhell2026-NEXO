import io
from datetime import timedelta
from unittest import mock

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from core.plazos import sumar_dias_habiles
from core.testutils import crear_cliente, crear_expediente, crear_juzgado, crear_usuario, radicado
from expedientes.models import DocumentoExpediente, EtapaProceso, Expediente, Juzgado
from expedientes.validators import formatear_radicado, normalizar_radicado, validar_radicado
from facturacion.models import Factura


class RadicadoTests(SimpleTestCase):
    def test_acepta_radicado_valido_con_separadores(self):
        self.assertEqual(validar_radicado("11001 31 03 012 2025 00123 00"), "11001310301220250012300")
        self.assertEqual(validar_radicado("11001-31-03-012-2025-00123-00"), "11001310301220250012300")

    def test_rechaza_longitud_incorrecta(self):
        with self.assertRaisesMessage(ValidationError, "23 dígitos"):
            validar_radicado("15347658009809764532")  # 20 dígitos

    def test_rechaza_letras(self):
        with self.assertRaises(ValidationError):
            validar_radicado("1100131030122025001230A")

    def test_rechaza_anio_imposible(self):
        with self.assertRaisesMessage(ValidationError, "año"):
            validar_radicado("11001310301220990012300")

    def test_rechaza_campos_en_cero(self):
        with self.assertRaises(ValidationError):
            validar_radicado("00000310301220250012300")  # municipio 00000
        with self.assertRaises(ValidationError):
            validar_radicado("11001310300020250012300")  # despacho 000

    def test_normalizar_y_formatear(self):
        self.assertEqual(normalizar_radicado(" 11001-31 03.012 "), "110013103012")
        self.assertEqual(formatear_radicado("11001310301220250012300"), "11001 31 03 012 2025 00123 00")


class BaseApi(APITestCase):
    def setUp(self):
        self.admin = crear_usuario("admin1", "administrador")
        self.socio = crear_usuario("socio1", "socio_director")
        self.abogado = crear_usuario("abog1", "abogado")
        self.otro = crear_usuario("abog2", "abogado")
        self.exp_propio = crear_expediente(self.abogado)
        self.exp_ajeno = crear_expediente(self.otro)

    def como(self, usuario):
        self.client.force_authenticate(usuario)


class ExpedienteApiTests(BaseApi):
    def datos(self, **extra):
        d = {
            "numero": radicado(),
            "juzgado": crear_juzgado().pk,
            "demandante": "Ana María López",
            "demandado": "Empresa de Prueba S.A.S.",
            "materia": "Civil",
            "estado": "activo",
        }
        d.update(extra)
        return d

    def test_rechaza_radicado_invalido_con_mensaje_claro(self):
        self.como(self.abogado)
        r = self.client.post("/api/expedientes/", self.datos(numero="15347658009809764532"), format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("23 dígitos", str(r.data["numero"][0]))

    def test_acepta_radicado_con_espacios_y_lo_guarda_normalizado(self):
        self.como(self.abogado)
        r = self.client.post("/api/expedientes/", self.datos(numero="11001 31 03 012 2025 00999 00"), format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["numero"], "11001310301220250099900")

    def test_radicado_repetido_aunque_cambie_el_formato(self):
        self.como(self.abogado)
        guardado = self.exp_propio.numero  # 23 dígitos juntos
        con_espacios = f"{guardado[:5]} {guardado[5:7]} {guardado[7:9]} {guardado[9:12]} {guardado[12:16]} {guardado[16:21]} {guardado[21:]}"
        r = self.client.post("/api/expedientes/", self.datos(numero=con_espacios), format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("Ya existe", str(r.data["numero"][0]))

    def test_editar_sin_cambiar_el_radicado_no_choca_consigo_mismo(self):
        self.como(self.abogado)
        r = self.client.patch(
            f"/api/expedientes/{self.exp_propio.pk}/", {"numero": self.exp_propio.numero, "materia": "Laboral"}, format="json"
        )
        self.assertEqual(r.status_code, 200, r.data)

    def test_expediente_antiguo_de_20_digitos_se_puede_editar_sin_tocar_el_numero(self):
        antiguo = crear_expediente(self.abogado, numero="15347658009809764532")
        self.como(self.abogado)
        r = self.client.patch(f"/api/expedientes/{antiguo.pk}/", {"numero": antiguo.numero, "materia": "Civil"}, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        # pero si intenta cambiarlo a otro número inválido, se rechaza
        r = self.client.patch(f"/api/expedientes/{antiguo.pk}/", {"numero": "12345"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_sin_abogado_se_asigna_a_quien_crea(self):
        self.como(self.abogado)
        r = self.client.post("/api/expedientes/", self.datos(), format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["abogado_asignado"], self.abogado.pk)

    def test_abogado_no_puede_asignar_a_otro_abogado(self):
        self.como(self.abogado)
        r = self.client.post("/api/expedientes/", self.datos(abogado_asignado=self.otro.pk), format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("abogado_asignado", r.data)

    def test_socio_si_puede_asignar_a_otro_abogado(self):
        self.como(self.socio)
        r = self.client.post("/api/expedientes/", self.datos(abogado_asignado=self.otro.pk), format="json")
        self.assertEqual(r.status_code, 201, r.data)

    def test_filtrado_por_rol(self):
        self.como(self.abogado)
        ids = [e["id"] for e in self.client.get("/api/expedientes/").data]
        self.assertEqual(ids, [self.exp_propio.pk])
        self.assertEqual(self.client.get(f"/api/expedientes/{self.exp_ajeno.pk}/").status_code, 404)

        for directivo in (self.admin, self.socio):
            self.como(directivo)
            self.assertEqual(len(self.client.get("/api/expedientes/").data), 2)

    def test_superusuario_ve_todo_aunque_su_rol_sea_abogado(self):
        # createsuperuser deja rol "abogado" por defecto; el superusuario debe tener acceso total.
        sup = crear_usuario("root", "abogado", is_superuser=True, is_staff=True)
        self.como(sup)
        self.assertEqual(len(self.client.get("/api/expedientes/").data), 2)

    def test_eliminar_expediente_con_facturas_responde_409(self):
        Factura.objects.create(numero="F-1", expediente=self.exp_propio, concepto="Honorarios", monto=1000)
        self.como(self.abogado)
        r = self.client.delete(f"/api/expedientes/{self.exp_propio.pk}/")
        self.assertEqual(r.status_code, 409)
        self.assertIn("facturas", r.data["detail"])
        self.assertTrue(Expediente.objects.filter(pk=self.exp_propio.pk).exists())

    def test_eliminar_expediente_sin_facturas(self):
        self.como(self.abogado)
        self.assertEqual(self.client.delete(f"/api/expedientes/{self.exp_propio.pk}/").status_code, 204)


class JuzgadoApiTests(BaseApi):
    def test_cualquier_usuario_puede_crear_juzgado(self):
        self.como(self.abogado)
        r = self.client.post("/api/juzgados/", {"nombre": "Juzgado 5 Laboral de Cali", "ciudad": "Cali", "materia": "laboral"}, format="json")
        self.assertEqual(r.status_code, 201, r.data)

    def test_solo_directivos_editan_o_borran(self):
        j = crear_juzgado()
        self.como(self.abogado)
        self.assertEqual(self.client.delete(f"/api/juzgados/{j.pk}/").status_code, 403)
        self.assertEqual(self.client.patch(f"/api/juzgados/{j.pk}/", {"ciudad": "Otra"}, format="json").status_code, 403)

    def test_no_se_borra_un_juzgado_con_expedientes(self):
        self.como(self.admin)
        r = self.client.delete(f"/api/juzgados/{self.exp_propio.juzgado.pk}/")
        self.assertEqual(r.status_code, 409)


class EtapaApiTests(BaseApi):
    def test_cada_usuario_ve_solo_las_etapas_de_sus_expedientes(self):
        propia = EtapaProceso.objects.create(expediente=self.exp_propio, nombre="Demanda")
        EtapaProceso.objects.create(expediente=self.exp_ajeno, nombre="Ajena")
        self.como(self.abogado)
        self.assertEqual([e["id"] for e in self.client.get("/api/etapas/").data], [propia.pk])

    def test_no_se_puede_crear_etapa_en_expediente_ajeno(self):
        self.como(self.abogado)
        r = self.client.post("/api/etapas/", {"expediente": self.exp_ajeno.pk, "nombre": "X", "orden": 1}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(EtapaProceso.objects.count(), 0)

    def test_fecha_limite_se_calcula_en_dias_habiles(self):
        self.como(self.abogado)
        r = self.client.post(
            "/api/etapas/",
            {"expediente": self.exp_propio.pk, "nombre": "Contestación", "dias_habiles": 5, "orden": 1},
            format="json",
        )
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["fecha_limite"], sumar_dias_habiles(timezone.localdate(), 5).isoformat())

    def test_fecha_explicita_tiene_prioridad_sobre_dias_habiles(self):
        self.como(self.abogado)
        r = self.client.post(
            "/api/etapas/",
            {"expediente": self.exp_propio.pk, "nombre": "X", "fecha_limite": "2030-01-15", "dias_habiles": 5, "orden": 1},
            format="json",
        )
        self.assertEqual(r.data["fecha_limite"], "2030-01-15")

    def test_dias_restantes(self):
        EtapaProceso.objects.create(expediente=self.exp_propio, nombre="Vencida", fecha_limite=timezone.localdate() - timedelta(days=2))
        self.como(self.abogado)
        etapas = self.client.get("/api/etapas/").data
        self.assertEqual(etapas[0]["dias_restantes"], -2)


class HistorialApiTests(BaseApi):
    def test_registra_quien_creo_y_quien_modifico(self):
        self.como(self.abogado)
        datos = {
            "numero": radicado(), "juzgado": crear_juzgado().pk, "demandante": "Ana María López",
            "demandado": "Empresa de Prueba", "materia": "Civil", "estado": "activo",
        }
        creado = self.client.post("/api/expedientes/", datos, format="json").data
        self.client.patch(f"/api/expedientes/{creado['id']}/", {"estado": "tramite"}, format="json")

        eventos = self.client.get(f"/api/expedientes/{creado['id']}/historial/").data
        self.assertEqual([e["tipo"] for e in eventos], ["Modificación", "Creación"])
        nombre = self.abogado.get_full_name()
        self.assertEqual(eventos[0]["usuario"], nombre)
        self.assertEqual(eventos[1]["usuario"], nombre)
        self.assertEqual(
            eventos[0]["cambios"], [{"campo": "Estado", "anterior": "Activo", "nuevo": "En trámite"}]
        )

    def test_muestra_nombres_en_lugar_de_ids(self):
        self.como(self.socio)
        self.client.patch(f"/api/expedientes/{self.exp_propio.pk}/", {"abogado_asignado": self.otro.pk}, format="json")
        eventos = self.client.get(f"/api/expedientes/{self.exp_propio.pk}/historial/").data
        cambio = eventos[0]["cambios"][0]
        self.assertEqual(cambio["campo"], "Abogado asignado")
        self.assertEqual(cambio["anterior"], self.abogado.get_full_name())
        self.assertEqual(cambio["nuevo"], self.otro.get_full_name())

    def test_no_se_ve_el_historial_de_un_expediente_ajeno(self):
        self.como(self.abogado)
        self.assertEqual(self.client.get(f"/api/expedientes/{self.exp_ajeno.pk}/historial/").status_code, 404)


class DocumentosApiTests(BaseApi):
    def url(self, exp=None, doc=None):
        exp = exp or self.exp_propio
        base = f"/api/expedientes/{exp.pk}/documentos/"
        return base + (f"{doc}/" if doc else "")

    def subir(self, nombre="demanda.pdf", contenido=b"%PDF-1.4 contenido de prueba", exp=None):
        archivo = SimpleUploadedFile(nombre, contenido, content_type="application/pdf")
        return self.client.post(self.url(exp), {"archivo": archivo}, format="multipart")

    def test_subir_listar_y_descargar(self):
        self.como(self.abogado)
        r = self.subir()
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["nombre"], "demanda.pdf")
        self.assertEqual(r.data["tamano"], len(b"%PDF-1.4 contenido de prueba"))
        self.assertNotIn("contenido", r.data)

        lista = self.client.get(self.url()).data
        self.assertEqual(len(lista), 1)

        descarga = self.client.get(self.url(doc=r.data["id"]))
        self.assertEqual(descarga.status_code, 200)
        self.assertEqual(descarga.content, b"%PDF-1.4 contenido de prueba")
        self.assertIn("attachment", descarga["Content-Disposition"])

    def test_rechaza_extension_no_permitida(self):
        self.como(self.abogado)
        r = self.subir(nombre="virus.exe")
        self.assertEqual(r.status_code, 400)
        self.assertIn("no permitido", r.data["detail"])

    def test_rechaza_archivo_vacio_y_sin_archivo(self):
        self.como(self.abogado)
        self.assertEqual(self.subir(contenido=b"").status_code, 400)
        self.assertEqual(self.client.post(self.url(), {}, format="multipart").status_code, 400)

    def test_rechaza_archivo_demasiado_grande(self):
        self.como(self.abogado)
        with mock.patch.object(DocumentoExpediente, "TAMANO_MAXIMO", 10):
            r = self.subir(contenido=b"x" * 11)
        self.assertEqual(r.status_code, 400)
        self.assertIn("tamaño máximo", r.data["detail"])

    def test_no_se_accede_a_documentos_de_expediente_ajeno(self):
        self.como(self.otro)
        self.assertEqual(self.subir(exp=self.exp_propio).status_code, 404)
        self.como(self.abogado)
        doc = self.subir().data
        self.como(self.otro)
        self.assertEqual(self.client.get(self.url(doc=doc["id"])).status_code, 404)

    def test_eliminar_documento(self):
        self.como(self.abogado)
        doc = self.subir().data
        self.assertEqual(self.client.delete(self.url(doc=doc["id"])).status_code, 204)
        self.assertEqual(DocumentoExpediente.objects.count(), 0)

    def test_directivo_puede_eliminar_documento_de_otro(self):
        self.como(self.abogado)
        doc = self.subir().data
        self.como(self.admin)
        self.assertEqual(self.client.delete(self.url(doc=doc["id"])).status_code, 204)

    def test_documento_inexistente(self):
        self.como(self.abogado)
        self.assertEqual(self.client.get(self.url(doc=99999)).status_code, 404)


class DashboardApiTests(BaseApi):
    def test_estadisticas_respetan_el_rol(self):
        self.como(self.abogado)
        self.assertEqual(self.client.get("/api/dashboard/stats/").data["casos_activos"], 1)
        self.como(self.admin)
        self.assertEqual(self.client.get("/api/dashboard/stats/").data["casos_activos"], 2)

    def test_plazos_a_atender_incluyen_vencidos_y_proximos_pero_no_lejanos_ni_completados(self):
        hoy = timezone.localdate()
        EtapaProceso.objects.create(expediente=self.exp_propio, nombre="Vencida", fecha_limite=hoy - timedelta(days=1))
        EtapaProceso.objects.create(expediente=self.exp_propio, nombre="Próxima", fecha_limite=hoy + timedelta(days=3))
        EtapaProceso.objects.create(expediente=self.exp_propio, nombre="Lejana", fecha_limite=hoy + timedelta(days=60))
        EtapaProceso.objects.create(expediente=self.exp_propio, nombre="Hecha", fecha_limite=hoy - timedelta(days=5), estado="completada")
        self.como(self.abogado)
        datos = self.client.get("/api/dashboard/stats/").data
        self.assertEqual(datos["plazos_procesales"], 2)
        self.assertEqual(datos["plazos_vencidos"], 1)

    def test_ingresos_del_mes_solo_cuentan_facturas_pagadas(self):
        Factura.objects.create(numero="F-1", expediente=self.exp_propio, concepto="Pendiente", monto=1000, estado="pendiente")
        Factura.objects.create(
            numero="F-2", expediente=self.exp_propio, concepto="Pagada", monto=2500, estado="pagada",
            fecha_pago=timezone.localdate(),
        )
        self.como(self.abogado)
        datos = self.client.get("/api/dashboard/stats/").data
        self.assertEqual(float(datos["ingresos_mes"]), 2500.0)
        self.assertEqual(float(datos["por_cobrar"]), 1000.0)


class DespachosRamaJudicialTests(BaseApi):
    def test_interpreta_el_formato_de_la_rama_judicial(self):
        from expedientes.despachos import interpretar_despacho

        d = interpretar_despacho("110013109032 - JUZGADO 032 PENAL DEL CIRCUITO CON FUNCIÓN DE CONOCIMIENTO DE BOGOTÁ")
        self.assertEqual(d["codigo"], "110013109032")
        self.assertEqual(d["departamento"], "BOGOTÁ, D.C.")
        self.assertEqual(d["municipio"], "BOGOTÁ")
        self.assertEqual(d["entidad"], "JUZGADO DE CIRCUITO")
        self.assertEqual(d["especialidad"], "PENAL")

    def test_tribunal_no_toma_el_departamento_como_municipio(self):
        from expedientes.despachos import interpretar_despacho

        d = interpretar_despacho("050002213000 - SALA CIVIL FAMILIA DEL TRIBUNAL SUPERIOR DE ANTIOQUIA")
        self.assertEqual(d["departamento"], "ANTIOQUIA")
        self.assertEqual(d["municipio"], "")
        self.assertEqual(d["entidad"], "TRIBUNAL SUPERIOR")
        self.assertEqual(d["especialidad"], "CIVIL FAMILIA")

    def test_municipio_con_nombre_compuesto(self):
        from expedientes.despachos import interpretar_despacho

        d = interpretar_despacho("520013103001 - JUZGADO 001 CIVIL DEL CIRCUITO DE SAN JUAN DE PASTO")
        self.assertEqual(d["municipio"], "SAN JUAN DE PASTO")

    def test_lineas_invalidas_se_ignoran(self):
        from expedientes.despachos import interpretar_despacho

        self.assertIsNone(interpretar_despacho("Todos"))
        self.assertIsNone(interpretar_despacho("123 - JUZGADO"))

    def test_importar_es_idempotente(self):
        import os
        import tempfile

        from django.core.management import call_command

        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("Todos\n110013109032 - JUZGADO 032 PENAL DEL CIRCUITO CON FUNCIÓN DE CONOCIMIENTO DE BOGOTÁ\n")
            ruta = f.name
        try:
            call_command("importar_despachos", ruta, stdout=io.StringIO())
            call_command("importar_despachos", ruta, stdout=io.StringIO())
        finally:
            os.unlink(ruta)
        self.assertEqual(Juzgado.objects.filter(codigo="110013109032").count(), 1)

    def test_api_devuelve_etiqueta_y_valida_codigo(self):
        self.como(self.abogado)
        r = self.client.post("/api/juzgados/", {
            "nombre": "JUZGADO 004 CIVIL MUNICIPAL DE BOGOTÁ", "codigo": "110014003004",
            "departamento": "BOGOTÁ, D.C.", "municipio": "BOGOTÁ", "entidad": "JUZGADO MUNICIPAL", "especialidad": "CIVIL",
        }, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["etiqueta"], "110014003004 - JUZGADO 004 CIVIL MUNICIPAL DE BOGOTÁ")
        self.assertEqual(r.data["ciudad"], "BOGOTÁ")
        malo = self.client.post("/api/juzgados/", {"nombre": "Juzgado de prueba", "codigo": "123"}, format="json")
        self.assertEqual(malo.status_code, 400)


class EquivalenciaJuzgadosTests(BaseApi):
    def test_reasigna_expedientes_al_despacho_real(self):
        from django.core.management import call_command

        from expedientes.despachos import interpretar_despacho

        viejo = self.exp_propio.juzgado
        viejo.nombre, viejo.ciudad, viejo.codigo = "Juzgado 12 Civil del Circuito de Bogotá", "Bogotá D.C.", None
        viejo.save()
        for linea in (
            "110013103012 - JUZGADO 012 CIVIL DEL CIRCUITO DE BOGOTÁ",
            "110014003012 - JUZGADO 012 CIVIL MUNICIPAL DE BOGOTÁ",
            "110013103012 - JUZGADO 012 CIVIL DEL CIRCUITO DE BOGOTÁ",
        ):
            d = interpretar_despacho(linea)
            codigo = d.pop("codigo")
            Juzgado.objects.update_or_create(codigo=codigo, defaults=d)
        call_command("reasignar_juzgados_antiguos", "--aplicar", stdout=io.StringIO())
        self.exp_propio.refresh_from_db()
        self.assertEqual(self.exp_propio.juzgado.codigo, "110013103012")
        self.assertFalse(Juzgado.objects.filter(pk=viejo.pk).exists())
