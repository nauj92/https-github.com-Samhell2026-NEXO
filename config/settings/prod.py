from .base import *  # noqa
import dj_database_url
import os

DEBUG = False

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")

# Base de datos: Render inyecta esta variable automáticamente
DATABASES = {
    "default": dj_database_url.config(default=env("DATABASE_URL"))
}

# Seguridad
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
X_FRAME_OPTIONS = "DENY"

# Archivos estáticos servidos con whitenoise
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# CORS: se configura con la URL real del frontend una vez desplegado
CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")

# Enlace del frontend para el correo de recuperación de contraseña (por omisión, el primer origen CORS)
FRONTEND_URL = os.environ.get("FRONTEND_URL") or CORS_ALLOWED_ORIGINS[0]
