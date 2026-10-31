import re

from django.core import mail
from django.core.cache import cache
from rest_framework.test import APITestCase

from core.testutils import CLAVE, crear_usuario
from usuarios.models import Usuario


class LoginTests(APITestCase):
    def setUp(self):
        self.usuario = crear_usuario("abog1", "abogado")

    def test_login_correcto_devuelve_tokens(self):
        r = self.client.post("/api/token/", {"username": "abog1", "password": CLAVE}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertIn("access", r.data)
        self.assertIn("refresh", r.data)

    def test_login_con_clave_incorrecta(self):
        r = self.client.post("/api/token/", {"username": "abog1", "password": "mala"}, format="json")
        self.assertEqual(r.status_code, 401)

    def test_los_endpoints_protegidos_exigen_token(self):
        self.assertEqual(self.client.get("/api/expedientes/").status_code, 401)

    def test_el_token_permite_consultar_la_api(self):
        token = self.client.post("/api/token/", {"username": "abog1", "password": CLAVE}, format="json").data["access"]
        r = self.client.get("/api/perfil/", HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["username"], "abog1")


class PerfilYPasswordTests(APITestCase):
    def setUp(self):
        self.usuario = crear_usuario("abog1", "abogado")
        self.client.force_authenticate(self.usuario)

    def test_cambiar_password(self):
        r = self.client.post(
            "/api/perfil/cambiar-password/",
            {"password_actual": CLAVE, "password_nueva": "Nueva-Clave-Muy-Larga-77"},
            format="json",
        )
        self.assertEqual(r.status_code, 200, r.data)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password("Nueva-Clave-Muy-Larga-77"))

    def test_password_actual_incorrecta(self):
        r = self.client.post(
            "/api/perfil/cambiar-password/", {"password_actual": "no", "password_nueva": "Nueva-Clave-Muy-Larga-77"}, format="json"
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("actual", r.data["detail"])

    def test_password_nueva_debil(self):
        r = self.client.post(
            "/api/perfil/cambiar-password/", {"password_actual": CLAVE, "password_nueva": "12345678"}, format="json"
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("password_nueva", r.data)

    def test_el_perfil_no_permite_cambiar_el_rol(self):
        self.client.patch("/api/perfil/", {"rol": "administrador", "telefono": "3001234567"}, format="json")
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.rol, "abogado")
        self.assertEqual(self.usuario.telefono, "3001234567")


class GestionUsuariosTests(APITestCase):
    def setUp(self):
        self.admin = crear_usuario("admin1", "administrador")
        self.abogado = crear_usuario("abog1", "abogado")

    def nuevo(self, **extra):
        d = {
            "username": "nuevo1", "first_name": "Nuevo", "last_name": "Usuario", "email": "nuevo1@example.com",
            "rol": "secretario_juridico", "password": "Clave-Inicial-Segura-91",
        }
        d.update(extra)
        return d

    def test_un_abogado_no_puede_gestionar_usuarios(self):
        self.client.force_authenticate(self.abogado)
        self.assertEqual(self.client.get("/api/gestion-usuarios/").status_code, 403)
        self.assertEqual(self.client.post("/api/gestion-usuarios/", self.nuevo(), format="json").status_code, 403)

    def test_el_admin_lista_usuarios_sin_exponer_contrasenas(self):
        self.client.force_authenticate(self.admin)
        r = self.client.get("/api/gestion-usuarios/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data), 2)
        self.assertNotIn("password", r.data[0])

    def test_crear_usuario_que_luego_puede_iniciar_sesion(self):
        self.client.force_authenticate(self.admin)
        r = self.client.post("/api/gestion-usuarios/", self.nuevo(), format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertNotIn("password", r.data)
        self.client.force_authenticate(None)
        login = self.client.post("/api/token/", {"username": "nuevo1", "password": "Clave-Inicial-Segura-91"}, format="json")
        self.assertEqual(login.status_code, 200)

    def test_crear_exige_contrasena_segura_y_datos_completos(self):
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.post("/api/gestion-usuarios/", self.nuevo(password="12345678"), format="json").status_code, 400)
        sin_clave = self.nuevo()
        del sin_clave["password"]
        r = self.client.post("/api/gestion-usuarios/", sin_clave, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("password", r.data)
        self.assertEqual(self.client.post("/api/gestion-usuarios/", self.nuevo(email=""), format="json").status_code, 400)

    def test_usuario_repetido(self):
        self.client.force_authenticate(self.admin)
        r = self.client.post("/api/gestion-usuarios/", self.nuevo(username="abog1"), format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("username", r.data)

    def test_cambiar_rol_y_desactivar_a_otro_usuario(self):
        self.client.force_authenticate(self.admin)
        r = self.client.patch(f"/api/gestion-usuarios/{self.abogado.pk}/", {"rol": "socio_director", "is_active": False}, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        self.abogado.refresh_from_db()
        self.assertEqual(self.abogado.rol, "socio_director")
        self.assertFalse(self.abogado.is_active)

    def test_el_admin_no_puede_desactivarse_ni_cambiarse_el_rol(self):
        self.client.force_authenticate(self.admin)
        url = f"/api/gestion-usuarios/{self.admin.pk}/"
        self.assertEqual(self.client.patch(url, {"is_active": False}, format="json").status_code, 400)
        self.assertEqual(self.client.patch(url, {"rol": "abogado"}, format="json").status_code, 400)

    def test_restablecer_contrasena_de_otro_usuario(self):
        self.client.force_authenticate(self.admin)
        r = self.client.patch(f"/api/gestion-usuarios/{self.abogado.pk}/", {"password": "Otra-Clave-Segura-55"}, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        self.abogado.refresh_from_db()
        self.assertTrue(self.abogado.check_password("Otra-Clave-Segura-55"))

    def test_no_se_puede_borrar_usuarios(self):
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.delete(f"/api/gestion-usuarios/{self.abogado.pk}/").status_code, 405)

    def test_desbloquear(self):
        self.client.force_authenticate(self.admin)
        r = self.client.post(f"/api/gestion-usuarios/{self.abogado.pk}/desbloquear/")
        self.assertEqual(r.status_code, 200, r.data)

    def test_la_lista_simple_solo_trae_usuarios_activos(self):
        inactivo = crear_usuario("abog9", "abogado")
        inactivo.is_active = False
        inactivo.save()
        self.client.force_authenticate(self.abogado)
        nombres = [u["username"] for u in self.client.get("/api/usuarios/").data]
        self.assertIn("abog1", nombres)
        self.assertNotIn("abog9", nombres)


class RecuperacionPasswordTests(APITestCase):
    def setUp(self):
        cache.clear()  # reinicia el límite de solicitudes entre pruebas
        self.usuario = crear_usuario("abog1", "abogado")

    def solicitar(self, email):
        return self.client.post("/api/password-reset/", {"email": email}, format="json")

    def enlace(self):
        cuerpo = mail.outbox[-1].body
        return re.search(r"/restablecer/([^/\s]+)/([^\s]+)", cuerpo).groups()

    def test_envia_correo_con_enlace(self):
        r = self.solicitar("abog1@example.com")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["abog1@example.com"])
        self.assertIn("/restablecer/", mail.outbox[0].body)

    def test_responde_igual_si_el_correo_no_existe(self):
        existente = self.solicitar("abog1@example.com").data
        inexistente = self.solicitar("nadie@example.com")
        self.assertEqual(inexistente.status_code, 200)
        self.assertEqual(inexistente.data, existente)
        self.assertEqual(len(mail.outbox), 1)  # solo el del correo real

    def test_no_envia_a_usuarios_inactivos(self):
        self.usuario.is_active = False
        self.usuario.save()
        self.solicitar("abog1@example.com")
        self.assertEqual(len(mail.outbox), 0)

    def test_correo_con_formato_invalido(self):
        self.assertEqual(self.solicitar("esto-no-es-un-correo").status_code, 400)

    def test_flujo_completo(self):
        self.solicitar("abog1@example.com")
        uid, token = self.enlace()
        r = self.client.post(
            "/api/password-reset/confirmar/", {"uid": uid, "token": token, "password_nueva": "Clave-Recuperada-88"}, format="json"
        )
        self.assertEqual(r.status_code, 200, r.data)
        login = self.client.post("/api/token/", {"username": "abog1", "password": "Clave-Recuperada-88"}, format="json")
        self.assertEqual(login.status_code, 200)

    def test_el_enlace_solo_sirve_una_vez(self):
        self.solicitar("abog1@example.com")
        uid, token = self.enlace()
        datos = {"uid": uid, "token": token, "password_nueva": "Clave-Recuperada-88"}
        self.assertEqual(self.client.post("/api/password-reset/confirmar/", datos, format="json").status_code, 200)
        datos["password_nueva"] = "Otra-Clave-Recuperada-99"
        self.assertEqual(self.client.post("/api/password-reset/confirmar/", datos, format="json").status_code, 400)

    def test_token_invalido(self):
        self.solicitar("abog1@example.com")
        uid, _ = self.enlace()
        r = self.client.post(
            "/api/password-reset/confirmar/", {"uid": uid, "token": "token-falso", "password_nueva": "Clave-Recuperada-88"}, format="json"
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("enlace", r.data["detail"])

    def test_uid_invalido(self):
        r = self.client.post(
            "/api/password-reset/confirmar/", {"uid": "!!!", "token": "x", "password_nueva": "Clave-Recuperada-88"}, format="json"
        )
        self.assertEqual(r.status_code, 400)

    def test_password_debil_no_se_acepta_y_el_enlace_sigue_vigente(self):
        self.solicitar("abog1@example.com")
        uid, token = self.enlace()
        r = self.client.post(
            "/api/password-reset/confirmar/", {"uid": uid, "token": token, "password_nueva": "12345678"}, format="json"
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("password_nueva", r.data)
        ok = self.client.post(
            "/api/password-reset/confirmar/", {"uid": uid, "token": token, "password_nueva": "Clave-Recuperada-88"}, format="json"
        )
        self.assertEqual(ok.status_code, 200)

    def test_funciona_aunque_el_navegador_envie_un_token_vencido(self):
        # El frontend adjunta el token guardado; el endpoint público debe ignorarlo.
        r = self.client.post(
            "/api/password-reset/", {"email": "abog1@example.com"}, format="json", HTTP_AUTHORIZATION="Bearer token.vencido.xyz"
        )
        self.assertEqual(r.status_code, 200)


class DatosProfesionalesTests(APITestCase):
    def setUp(self):
        self.admin = crear_usuario("admin1", "administrador")
        self.abogado = crear_usuario("abog1", "abogado")

    def test_directivo_crea_abogado_con_cedula_y_tarjeta_profesional(self):
        self.client.force_authenticate(self.admin)
        r = self.client.post("/api/gestion-usuarios/", {
            "username": "camila", "first_name": "Camila", "last_name": "Herrera", "email": "camila@despacho.com",
            "rol": "abogado", "password": "Clave-Segura-2026!", "cedula": "31.000.000", "tarjeta_profesional": "123456",
        }, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["cedula"], "31000000")
        self.assertEqual(r.data["tarjeta_profesional"], "123456")

    def test_cedula_y_tarjeta_invalidas_se_rechazan(self):
        self.client.force_authenticate(self.admin)
        base = {"username": "camila", "first_name": "Camila", "last_name": "Herrera", "email": "camila@despacho.com",
                "rol": "abogado", "password": "Clave-Segura-2026!"}
        self.assertEqual(self.client.post("/api/gestion-usuarios/", {**base, "cedula": "abc"}, format="json").status_code, 400)
        self.assertEqual(self.client.post("/api/gestion-usuarios/", {**base, "tarjeta_profesional": "1"}, format="json").status_code, 400)

    def test_el_listado_para_seleccionar_abogados_trae_sus_datos_profesionales(self):
        Usuario.objects.filter(pk=self.abogado.pk).update(cedula="31000000", tarjeta_profesional="123456")
        self.client.force_authenticate(self.abogado)
        fila = next(u for u in self.client.get("/api/usuarios/").data if u["username"] == "abog1")
        self.assertEqual((fila["cedula"], fila["tarjeta_profesional"], fila["email"]), ("31000000", "123456", "abog1@example.com"))

    def test_un_abogado_no_puede_crear_usuarios(self):
        self.client.force_authenticate(self.abogado)
        self.assertEqual(self.client.post("/api/gestion-usuarios/", {}, format="json").status_code, 403)


class PrimerIngresoTests(APITestCase):
    """El administrador crea las cuentas; la persona cambia la clave y autoriza el uso de sus datos."""

    TEMPORAL = "Clave-Inicial-Segura-91"

    def setUp(self):
        self.admin = crear_usuario("admin1", "administrador")
        self.socio = crear_usuario("socio1", "socio_director")
        self.abogado = crear_usuario("abog1", "abogado")

    def datos(self, **extra):
        d = {
            "username": "nuevo1", "first_name": "Nuevo", "last_name": "Usuario", "email": "nuevo1@example.com",
            "rol": "escribiente", "password": self.TEMPORAL,
        }
        d.update(extra)
        return d

    def crear_y_entrar(self, **extra):
        """El administrador crea la cuenta y la persona inicia sesión con la clave temporal."""
        self.client.force_authenticate(self.admin)
        r = self.client.post("/api/gestion-usuarios/", self.datos(**extra), format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.client.force_authenticate(None)
        token = self.client.post(
            "/api/token/", {"username": extra.get("username", "nuevo1"), "password": self.TEMPORAL}, format="json"
        ).data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return r

    def test_solo_el_administrador_crea_usuarios(self):
        for usuario in (self.socio, self.abogado):
            self.client.force_authenticate(usuario)
            r = self.client.post("/api/gestion-usuarios/", self.datos(), format="json")
            self.assertEqual(r.status_code, 403, usuario.username)
        self.assertFalse(Usuario.objects.filter(username="nuevo1").exists())

    def test_el_socio_consulta_pero_no_modifica(self):
        self.client.force_authenticate(self.socio)
        self.assertEqual(self.client.get("/api/gestion-usuarios/").status_code, 200)
        r = self.client.patch(f"/api/gestion-usuarios/{self.abogado.pk}/", {"is_active": False}, format="json")
        self.assertEqual(r.status_code, 403)
        self.assertEqual(self.client.post(f"/api/gestion-usuarios/{self.abogado.pk}/desbloquear/").status_code, 403)

    def test_se_crean_todos_los_roles_del_despacho(self):
        self.client.force_authenticate(self.admin)
        for i, rol in enumerate(["abogado", "secretario_juridico", "escribiente", "cliente"]):
            r = self.client.post(
                "/api/gestion-usuarios/", self.datos(username=f"usuario{i}", email=f"usuario{i}@example.com", rol=rol), format="json"
            )
            self.assertEqual(r.status_code, 201, r.data)
            self.assertEqual(r.data["rol"], rol)

    def test_crear_envia_correo_de_bienvenida(self):
        mail.outbox.clear()
        r = self.crear_y_entrar()
        self.assertTrue(r.data["correo_enviado"])
        self.assertEqual(len(mail.outbox), 1)
        correo = mail.outbox[0]
        self.assertEqual(correo.to, ["nuevo1@example.com"])
        self.assertIn("nuevo1", correo.body)
        self.assertIn(self.TEMPORAL, correo.body)
        self.assertIn("Escribiente", correo.body)
        self.assertIn("/login", correo.body)

    def test_si_el_correo_falla_la_cuenta_se_crea_igual(self):
        from unittest import mock

        self.client.force_authenticate(self.admin)
        with mock.patch("usuarios.correos.send_mail", side_effect=OSError("sin red")):
            r = self.client.post("/api/gestion-usuarios/", self.datos(), format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertFalse(r.data["correo_enviado"])
        self.assertTrue(Usuario.objects.filter(username="nuevo1").exists())

    def test_la_cuenta_nueva_queda_pendiente_de_primer_ingreso(self):
        r = self.crear_y_entrar()
        self.assertTrue(r.data["debe_cambiar_password"])
        self.assertTrue(r.data["autorizacion_datos_pendiente"])
        perfil = self.client.get("/api/perfil/")
        self.assertEqual(perfil.status_code, 200)
        self.assertTrue(perfil.data["debe_cambiar_password"])
        self.assertTrue(perfil.data["autorizacion_datos_pendiente"])

    def test_pendiente_no_puede_usar_el_sistema(self):
        self.crear_y_entrar(rol="abogado")
        r = self.client.get("/api/expedientes/")
        self.assertEqual(r.status_code, 403)
        self.assertIn("cambiar su contraseña", r.data["detail"])
        self.assertEqual(self.client.get("/api/dashboard/resumen/").status_code, 403)

    def test_flujo_completo_cambia_clave_autoriza_y_ya_puede_entrar(self):
        self.crear_y_entrar(rol="abogado")
        nueva = "Mi-Nueva-Clave-Larga-55"
        r = self.client.post(
            "/api/perfil/cambiar-password/", {"password_actual": self.TEMPORAL, "password_nueva": nueva}, format="json"
        )
        self.assertEqual(r.status_code, 200, r.data)
        # Falta la autorización de datos: sigue bloqueado
        self.assertEqual(self.client.get("/api/expedientes/").status_code, 403)
        r = self.client.post("/api/perfil/autorizar-datos/", {"acepto": True}, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(self.client.get("/api/expedientes/").status_code, 200)
        u = Usuario.objects.get(username="nuevo1")
        self.assertFalse(u.debe_cambiar_password)
        self.assertFalse(u.autorizacion_datos_pendiente)
        self.assertIsNotNone(u.fecha_autorizacion_datos)

    def test_la_autorizacion_exige_aceptar_expresamente(self):
        self.crear_y_entrar()
        for cuerpo in ({}, {"acepto": False}, {"acepto": "si"}):
            r = self.client.post("/api/perfil/autorizar-datos/", cuerpo, format="json")
            self.assertEqual(r.status_code, 400, cuerpo)
        self.assertTrue(Usuario.objects.get(username="nuevo1").autorizacion_datos_pendiente)

    def test_la_clave_nueva_debe_ser_distinta_de_la_temporal(self):
        self.crear_y_entrar()
        r = self.client.post(
            "/api/perfil/cambiar-password/", {"password_actual": self.TEMPORAL, "password_nueva": self.TEMPORAL}, format="json"
        )
        self.assertEqual(r.status_code, 400)
        self.assertTrue(Usuario.objects.get(username="nuevo1").debe_cambiar_password)

    def test_pendiente_tampoco_usa_la_gestion_de_usuarios(self):
        # Un administrador recién creado también debe completar su primer ingreso
        self.crear_y_entrar(username="admin2", email="admin2@example.com", rol="administrador")
        self.assertEqual(self.client.get("/api/gestion-usuarios/").status_code, 403)

    def test_el_administrador_que_fija_una_clave_obliga_a_cambiarla(self):
        self.client.force_authenticate(self.admin)
        r = self.client.patch(f"/api/gestion-usuarios/{self.abogado.pk}/", {"password": "Otra-Clave-Segura-55"}, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        self.abogado.refresh_from_db()
        self.assertTrue(self.abogado.debe_cambiar_password)

    def test_cuentas_existentes_no_quedan_bloqueadas(self):
        self.client.force_authenticate(self.abogado)
        self.assertEqual(self.client.get("/api/expedientes/").status_code, 200)

    def test_el_cliente_solo_ve_su_perfil(self):
        u = crear_usuario("cli1", "cliente")
        self.client.force_authenticate(u)
        self.assertEqual(self.client.get("/api/perfil/").status_code, 200)
        for ruta in ("/api/expedientes/", "/api/clientes/", "/api/demandas/", "/api/dashboard/resumen/", "/api/usuarios/"):
            self.assertEqual(self.client.get(ruta).status_code, 403, ruta)

    def test_el_perfil_informa_si_es_administrador(self):
        self.client.force_authenticate(self.admin)
        self.assertTrue(self.client.get("/api/perfil/").data["es_administrador"])
        self.client.force_authenticate(self.socio)
        self.assertFalse(self.client.get("/api/perfil/").data["es_administrador"])
