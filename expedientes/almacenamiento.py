"""Almacenamiento externo (opcional) de los documentos de los expedientes.

Por defecto los archivos se guardan en la base de datos (límite de 5 MB), porque el disco de los servicios
gratuitos de Render no es persistente. Si se define DOCUMENTOS_BUCKET, los archivos nuevos se guardan en un
servicio compatible con S3 (Amazon S3, Cloudflare R2, Backblaze B2, Supabase Storage, MinIO...) y el límite
sube a 25 MB. Los documentos que ya estaban en la base de datos se siguen leyendo normalmente.

Variables de entorno: DOCUMENTOS_BUCKET, DOCUMENTOS_ACCESS_KEY_ID, DOCUMENTOS_SECRET_ACCESS_KEY y, según el
proveedor, DOCUMENTOS_ENDPOINT_URL y DOCUMENTOS_REGION. Requiere instalar `boto3`.
"""
import logging
import re
import uuid

from django.conf import settings

logger = logging.getLogger(__name__)


class ErrorAlmacenamiento(Exception):
    """El almacenamiento externo no respondió o está mal configurado."""


def configurado():
    return bool(getattr(settings, "DOCUMENTOS_BUCKET", ""))


def _cliente():
    try:
        import boto3
    except ImportError as exc:
        raise ErrorAlmacenamiento("Falta instalar boto3 para usar el almacenamiento externo.") from exc
    return boto3.client(
        "s3",
        endpoint_url=getattr(settings, "DOCUMENTOS_ENDPOINT_URL", "") or None,
        region_name=getattr(settings, "DOCUMENTOS_REGION", "") or None,
        aws_access_key_id=getattr(settings, "DOCUMENTOS_ACCESS_KEY_ID", "") or None,
        aws_secret_access_key=getattr(settings, "DOCUMENTOS_SECRET_ACCESS_KEY", "") or None,
    )


def _ruta(expediente_id, nombre):
    seguro = re.sub(r"[^A-Za-z0-9._-]", "_", nombre)[:100] or "archivo"
    return f"expedientes/{expediente_id}/{uuid.uuid4().hex}-{seguro}"


def guardar(expediente_id, nombre, datos, tipo_contenido=""):
    """Sube el archivo y devuelve su ruta dentro del bucket."""
    ruta = _ruta(expediente_id, nombre)
    try:
        _cliente().put_object(
            Bucket=settings.DOCUMENTOS_BUCKET, Key=ruta, Body=datos, ContentType=tipo_contenido or "application/octet-stream"
        )
    except ErrorAlmacenamiento:
        raise
    except Exception as exc:
        logger.exception("No se pudo subir %s al almacenamiento externo", ruta)
        raise ErrorAlmacenamiento("No se pudo guardar el archivo en el almacenamiento externo.") from exc
    return ruta


def leer(ruta):
    try:
        return _cliente().get_object(Bucket=settings.DOCUMENTOS_BUCKET, Key=ruta)["Body"].read()
    except ErrorAlmacenamiento:
        raise
    except Exception as exc:
        logger.exception("No se pudo leer %s del almacenamiento externo", ruta)
        raise ErrorAlmacenamiento("No se pudo leer el archivo del almacenamiento externo.") from exc


def borrar(ruta):
    """Elimina el archivo. Nunca lanza: si falla queda en el registro del servidor."""
    try:
        _cliente().delete_object(Bucket=settings.DOCUMENTOS_BUCKET, Key=ruta)
    except Exception:
        logger.exception("No se pudo borrar %s del almacenamiento externo", ruta)
