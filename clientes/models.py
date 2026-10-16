from django.db import models


class Cliente(models.Model):
    nombre = models.CharField(max_length=200)
    tipo_documento = models.CharField(max_length=20, default="CC")
    numero_documento = models.CharField(max_length=30, unique=True)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["nombre"]
